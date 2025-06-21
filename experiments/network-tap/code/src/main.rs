use retina_core::config::load_config;
use retina_core::protocols::packet::{ethernet::*, ipv4::*, ipv6::*, udp::*, Packet};
use retina_core::FiveTuple;
use retina_core::{CoreId, Runtime};
use retina_datatypes::*;
use retina_filtergen::{filter, retina_main};

use std::collections::HashMap;
use std::io::Write;
use std::path::PathBuf;
use std::sync::atomic::{AtomicPtr, AtomicUsize, Ordering};
use std::sync::OnceLock;

use array_init::array_init;
use clap::Parser;
use serde::Serialize;

// Argument parsing
#[derive(Parser, Debug)]
struct Args {
    #[clap(short, long, parse(from_os_str), value_name = "FILE")]
    config: PathBuf,
    #[clap(
        short,
        long,
        parse(from_os_str),
        value_name = "FILE",
        default_value = "tuples.jsonl"
    )]
    outfile: PathBuf,
}

// Number of cores being used by the runtime; should match config file
// Should be defined at compile-time so that we can use a
// statically-sized array for RESULTS
const NUM_CORES: usize = 16;
// Add 1 for ARR_LEN to avoid overflow; one core is used as main_core
const ARR_LEN: usize = NUM_CORES + 1;

// Tuple counts for easy tracking
#[derive(Serialize, Default, Debug)]
struct TupleCounter {
    pub tuple: usize,
}

impl TupleCounter {
    pub fn extend(&mut self, other: &TupleCounter) {
        self.tuple += other.tuple;
    }
}

type TupleResults = HashMap<String, TupleCounter>;

// Map tuple counts
static UDP_TUPLE_COUNTS_PKT: OnceLock<[AtomicPtr<TupleResults>; ARR_LEN]> = OnceLock::new();
static UDP_TUPLE_COUNTS_CONN: OnceLock<[AtomicPtr<TupleResults>; ARR_LEN]> = OnceLock::new();
static PARSED_TUPLE_COUNTS_CONN: OnceLock<[AtomicPtr<HashMap<String, TupleResults>>; ARR_LEN]> =
    OnceLock::new();
static PARSED_TUPLE_COUNTS_PKT: OnceLock<[AtomicPtr<HashMap<String, TupleResults>>; ARR_LEN]> =
    OnceLock::new();

fn init_tuple_results() -> [AtomicPtr<TupleResults>; ARR_LEN] {
    let mut results = vec![];
    for _ in 0..ARR_LEN {
        results.push(Box::into_raw(Box::new(HashMap::new())));
    }
    array_init(|i| AtomicPtr::new(results[i]))
}

fn init_tuple_results_parsed() -> [AtomicPtr<HashMap<String, TupleResults>>; ARR_LEN] {
    let mut results = vec![];
    for _ in 0..ARR_LEN {
        results.push(Box::into_raw(Box::new(HashMap::new())));
    }
    array_init(|i| AtomicPtr::new(results[i]))
}

// Accessors
fn udp_tuple_counts_pkt() -> &'static [AtomicPtr<TupleResults>; ARR_LEN] {
    UDP_TUPLE_COUNTS_PKT.get_or_init(init_tuple_results)
}
fn udp_tuple_counts_conn() -> &'static [AtomicPtr<TupleResults>; ARR_LEN] {
    UDP_TUPLE_COUNTS_CONN.get_or_init(init_tuple_results)
}
fn parsed_tuple_counts_pkt() -> &'static [AtomicPtr<HashMap<String, TupleResults>>; ARR_LEN] {
    PARSED_TUPLE_COUNTS_PKT.get_or_init(init_tuple_results_parsed)
}
fn parsed_tuple_counts_conn() -> &'static [AtomicPtr<HashMap<String, TupleResults>>; ARR_LEN] {
    PARSED_TUPLE_COUNTS_CONN.get_or_init(init_tuple_results_parsed)
}

// To make it easier to calculate %s
static UDP_PKT_CNT: AtomicUsize = AtomicUsize::new(0);
static UDP_CONN_CNT: AtomicUsize = AtomicUsize::new(0);
static QUIC_PKT_CNT: AtomicUsize = AtomicUsize::new(0);
static QUIC_CONN_CNT: AtomicUsize = AtomicUsize::new(0);

// Ensure OnceLocks are all initialized
fn init() {
    let _ = udp_tuple_counts_pkt();
    let _ = udp_tuple_counts_conn();
    let _ = parsed_tuple_counts_pkt();
    let _ = parsed_tuple_counts_conn();
}

// Per-packet UDP callback
#[filter("udp")]
fn udp_pkt_cb(mbuf: &ZcFrame, core_id: &CoreId) {
    let mut src_port = None;
    let mut dst_port = None;
    if let Ok(eth) = &Packet::parse_to::<Ethernet>(mbuf) {
        if let Ok(ipv4) = &Packet::parse_to::<Ipv4>(eth) {
            if let Ok(udp) = &Packet::parse_to::<Udp>(ipv4) {
                src_port = Some(udp.src_port());
                dst_port = Some(udp.dst_port());
            }
        } else if let Ok(ipv6) = &Packet::parse_to::<Ipv6>(eth) {
            if let Ok(udp) = &Packet::parse_to::<Udp>(ipv6) {
                src_port = Some(udp.src_port());
                dst_port = Some(udp.dst_port());
            }
        }
    }

    if let (Some(src_port), Some(dst_port)) = (src_port, dst_port) {
        let key = format!("{}:{}", src_port, dst_port);
        let ptr = udp_tuple_counts_pkt()[core_id.raw() as usize].load(Ordering::Relaxed);
        let dict = unsafe { &mut *ptr };
        let entry = dict
            .entry(key)
            .or_insert(TupleCounter::default());
        entry.tuple += 1;
        UDP_PKT_CNT.fetch_add(1, Ordering::Relaxed);
    }
}

// Per-packet QUIC callback
#[filter("quic")]
fn quic_pkt_cb(mbuf: &ZcFrame, core_id: &CoreId) {
    let mut src_port = None;
    let mut dst_port = None;
    if let Ok(eth) = &Packet::parse_to::<Ethernet>(mbuf) {
        if let Ok(ipv4) = &Packet::parse_to::<Ipv4>(eth) {
            if let Ok(udp) = &Packet::parse_to::<Udp>(ipv4) {
                src_port = Some(udp.src_port());
                dst_port = Some(udp.dst_port());
            }
        } else if let Ok(ipv6) = &Packet::parse_to::<Ipv6>(eth) {
            if let Ok(udp) = &Packet::parse_to::<Udp>(ipv6) {
                src_port = Some(udp.src_port());
                dst_port = Some(udp.dst_port());
            }
        }
    }

    if let (Some(src_port), Some(dst_port)) = (src_port, dst_port) {
        let key = format!("{}:{}", src_port, dst_port);
        let ptr = udp_tuple_counts_pkt()[core_id.raw() as usize].load(Ordering::Relaxed);
        let dict = unsafe { &mut *ptr };
        let entry = dict
            .entry(key)
            .or_insert(TupleCounter::default());
        entry.tuple += 1;
        QUIC_PKT_CNT.fetch_add(1, Ordering::Relaxed);
    }
}

// Per-connection application-layer callbacks
fn insert_parsed_results(
    pkts: &PktCount,
    core_id: &CoreId,
    key: String,
    tuple_key: String,
) {
    let ptr = parsed_tuple_counts_conn()[core_id.raw() as usize].load(Ordering::Relaxed);
    let dict = unsafe { &mut *ptr };
    let entry = dict
        .entry(key.clone())
        .or_insert(HashMap::new())
        .entry(tuple_key.clone())
        .or_insert(TupleCounter::default());
    entry.tuple += 1;

    let ptr = parsed_tuple_counts_pkt()[core_id.raw() as usize].load(Ordering::Relaxed);
    let dict = unsafe { &mut *ptr };
    let entry = dict
        .entry(key.clone())
        .or_insert(HashMap::new())
        .entry(tuple_key.clone())
        .or_insert(TupleCounter::default());
    entry.tuple += pkts.raw();
}

// Per-connection UDP callback
#[filter("udp")]
fn udp_conn_cb(five_tuple: &FiveTuple, pkts: &PktCount, core_id: &CoreId) {
    let tuple_key = format!("{}:{}", five_tuple.orig.port(), five_tuple.resp.port());
    insert_parsed_results(pkts, core_id, String::from("udp"), tuple_key);
    UDP_CONN_CNT.fetch_add(1, Ordering::Relaxed);
}

// Per-connection QUIC callback
#[filter("quic")]
fn quic_conn_cb(five_tuple: &FiveTuple, pkts: &PktCount, core_id: &CoreId) {
    let tuple_key = format!("{}:{}", five_tuple.orig.port(), five_tuple.resp.port());
    insert_parsed_results(pkts, core_id, String::from("quic"), tuple_key);
    QUIC_CONN_CNT.fetch_add(1, Ordering::Relaxed);
}

// Combine results for easy serialization
#[derive(Serialize, Default)]
struct CombinedResults {
    pub udp_tuple_conns: TupleResults,
    pub udp_tuple_pkts: TupleResults,
    pub parsed_tuple_conns: HashMap<String, TupleResults>,
    pub parsed_tuple_pkts: HashMap<String, TupleResults>,
    pub udp_pkt_count: usize,
    pub udp_conn_count: usize,
    pub quic_conn_count: usize,
    pub quic_pkt_count: usize,
}

fn combine_results(outfile: &PathBuf) {
    let mut results = CombinedResults::default();
    for core_id in 0..ARR_LEN {
        // UDP tuple conn counts
        let ptr = udp_tuple_counts_conn()[core_id].load(Ordering::Relaxed);
        for (key, value) in unsafe { &*ptr } {
            results
                .udp_tuple_conns
                .entry(key.clone())
                .or_insert(TupleCounter::default())
                .extend(value);
        }

        // UDP tuple packet counts
        let ptr = udp_tuple_counts_pkt()[core_id].load(Ordering::Relaxed);
        for (key, value) in unsafe { &*ptr } {
            results
                .udp_tuple_pkts
                .entry(key.clone())
                .or_insert(TupleCounter::default())
                .extend(value);
        }

        // QUIC tuple conn counts
        let ptr = parsed_tuple_counts_conn()[core_id].load(Ordering::Relaxed);
        for (key, value) in unsafe { &*ptr } {
            let entry = results
                .parsed_tuple_conns
                .entry(key.clone())
                .or_insert(TupleResults::default());
            for (tuple, counters) in value {
                entry
                    .entry(tuple.clone())
                    .or_insert(TupleCounter::default())
                    .extend(counters);
            }
        }

        // QUIC tuple packet counts
        let ptr = parsed_tuple_counts_pkt()[core_id].load(Ordering::Relaxed);
        for (key, value) in unsafe { &*ptr } {
            let entry = results
                .parsed_tuple_pkts
                .entry(key.clone())
                .or_insert(TupleResults::default());
            for (tuple, counters) in value {
                entry
                    .entry(tuple.clone())
                    .or_insert(TupleCounter::default())
                    .extend(counters);
            }
        }
    }
    results.udp_pkt_count = UDP_PKT_CNT.load(Ordering::SeqCst);
    results.udp_conn_count = UDP_CONN_CNT.load(Ordering::SeqCst);
    results.quic_conn_count = QUIC_CONN_CNT.load(Ordering::SeqCst);
    results.quic_pkt_count = QUIC_PKT_CNT.load(Ordering::SeqCst);
    let mut file = std::fs::File::create(outfile).unwrap();
    let results = serde_json::to_string(&results).unwrap();
    file.write_all(results.as_bytes()).unwrap();
}

#[retina_main(4)]
fn main() {
    init();
    let args = Args::parse();
    let config = load_config(&args.config);
    let cores = config.get_all_rx_core_ids();
    let num_cores = cores.len();
    if num_cores > NUM_CORES {
        panic!(
            "Compile-time NUM_CORES ({}) must be <= num cores ({}) in config file",
            NUM_CORES, num_cores
        );
    }
    if cores.len() > 1 && !cores.windows(2).all(|w| w[1].raw() - w[0].raw() == 1) {
        panic!("Cores in config file should be consecutive for zero-lock indexing");
    }
    if cores[0].raw() > 1 {
        panic!("RX core IDs should start at 0 or 1");
    }
    let mut runtime: Runtime<SubscribedWrapper> = Runtime::new(config, filter).unwrap();
    runtime.run();
    combine_results(&args.outfile);
    println!(
        "Got {} udp packets, {} quic packets; {} udp, {} quic conns",
        UDP_PKT_CNT.load(Ordering::SeqCst),
        QUIC_PKT_CNT.load(Ordering::SeqCst),
        UDP_CONN_CNT.load(Ordering::SeqCst),
        QUIC_CONN_CNT.load(Ordering::SeqCst)
    );
}
