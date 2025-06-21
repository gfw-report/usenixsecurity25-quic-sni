use clap::{ArgAction, Parser};
use csv::Writer;
use log::{error, info, LevelFilter};
use std::collections::BinaryHeap;
use quiche::{ConnectionId, Config};
use rand::RngCore;
use std::{
    cmp::Ordering,
    collections::VecDeque,
    fs::File,
    io::{self, BufRead, BufReader, Write},
    net::{IpAddr, SocketAddr},
    sync::{
        atomic::{AtomicBool, AtomicUsize, Ordering as AtomicOrdering},
        Arc,
    },
    time::{Duration, Instant},
};
use tokio::{
    net::UdpSocket as TokioUdpSocket,
    sync::mpsc::{self, UnboundedReceiver, UnboundedSender},
    sync::Semaphore,
    task,
    time::sleep,
};
use chrono::Local;

use std::sync::Mutex as StdMutex; // Alias to avoid confusion
use tokio::sync::Mutex;
use rand::seq::SliceRandom;
use rand::thread_rng;
use socket2::{Socket, Domain, Type, Protocol};
use boring::ssl::{SslMethod,SslCurve};

// use quiche::{BoringSslCtxBuilder, Error};

// NEW: include the ipnet crate for subnet parsing
use ipnet::IpNet;

/// Maximum size for UDP datagrams
const MAX_DATAGRAM_SIZE: usize = 3500;

/// Command-line arguments structure
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Comma-separated list of destination IP addresses or subnets (e.g., "127.0.0.1,192.168.1.0/24,2001:db8::/120")
    #[arg(long, default_value = "127.0.0.1")]
    dip: String,

    /// Comma-separated list of destination ports
    #[arg(short, default_value = "10000-65000")]
    p: String,

    /// Comma-separated list of source ports
    #[arg(long)]
    sport: Option<String>,

    /// Number of workers in parallel
    #[arg(long, default_value = "100")]
    worker: usize,

    /// Residual cooldown duration (milliseconds)
    #[arg(long, default_value = "180000")]
    residual: u64,

    /// Output CSV file (default stdout)
    #[arg(long)]
    out: Option<String>,

    /// Log file (default stderr)
    #[arg(long)]
    log: Option<String>,

    /// Flush after every output
    #[arg(long, default_value = "true")]
    flush: bool,
    
    /// Input files with SNI values
    #[arg()]
    files: Vec<String>,

    /// Size of the socket pool
    #[arg(long, default_value = "1000")]
    socket_pool_size: usize,

    /// Trim trailing null bytes from the ClientHello packet
    #[arg(long, default_value_t = false)]
    trim_zeros: bool,

    /// Use srcports that are greater than dstports
    #[arg(long = "use-greater-srcports", default_value_t = true, action = ArgAction::Set)]
    #[arg(long = "no-use-greater-srcports", action = ArgAction::SetFalse)]
    use_greater_srcports: bool,

    /// Bind IP address for source sockets (IPv4 or IPv6)
    #[arg(long, default_value = "0.0.0.0")]
    bind_ip: String,

    /// Number of followup UDP payloads to send (default 5)
    #[arg(long, default_value_t = 5)]
    followup_payloads: usize,
}

/// Structure representing a port under cooldown
#[derive(Eq, PartialEq, Debug)]
struct CooldownPort {
    available_time: Instant,
    port: u16,
}

impl PartialOrd for CooldownPort {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        // Reverse the ordering for min-heap
        Some(other.available_time.cmp(&self.available_time))
    }
}

impl Ord for CooldownPort {
    fn cmp(&self, other: &Self) -> Ordering {
        // Reverse the ordering for min-heap
        other.available_time.cmp(&self.available_time)
    }
}

/// A pool of UDP sockets
struct SocketPool {
    /// Each socket is paired with its bound source port.
    sockets: Vec<(u16, Arc<TokioUdpSocket>)>,
    counter: AtomicUsize,
}

impl SocketPool {
    /// Initialize a new SocketPool with a given size, binding to the specified bind_ip.
    async fn new(size: usize, source_ports: Option<&Vec<u16>>, bind_ip: IpAddr) -> io::Result<Self> {
        let mut sockets = Vec::with_capacity(size);

        if let Some(ports) = source_ports {
            for &port in ports.iter() {
                if sockets.len() >= size {
                    break;
                }
                match Self::create_socket(bind_ip, Some(port)).await {
                    Ok(socket) => sockets.push((port, Arc::new(socket))),
                    Err(e) => {
                        error!("Failed to create socket on port {}: {}", port, e);
                        continue;
                    }
                }
            }
        }

        // If we need more sockets, create them with OS-chosen ports
        while sockets.len() < size {
            let socket = Self::create_socket(bind_ip, None).await?;
            let local_addr = socket.local_addr()?;
            let source_port = local_addr.port();
            sockets.push((source_port, Arc::new(socket)));
        }

        // Sort the sockets by source port for efficient lookup
        sockets.sort_by_key(|&(port, _)| port);

        Ok(Self {
            sockets,
            counter: AtomicUsize::new(0),
        })
    }

    /// Get a string representation of the socket pool's contents
    fn display(&self) -> String {
        let mut output = String::new();
        for (src_port, socket) in &self.sockets {
            // Get the local address of the socket
            let local_addr = match socket.local_addr() {
                Ok(addr) => addr.to_string(),
                Err(_) => "Unknown".to_string(),
            };
            output.push_str(&format!("Source Port: {}, Local Address: {}\n", src_port, local_addr));
        }
        output
    }

    /// Create a single UDP socket, binding to a specified port if provided.
    async fn create_socket(bind_ip: IpAddr, port: Option<u16>) -> io::Result<TokioUdpSocket> {
        let socket_addr = SocketAddr::new(bind_ip, port.unwrap_or(0));

        // Create a new socket using socket2
        let std_socket = Socket::new(
            Domain::for_address(socket_addr),
            Type::DGRAM,
            Some(Protocol::UDP),
        )?;

        std_socket.set_reuse_address(true)?;
        #[cfg(any(target_os = "linux", target_os = "macos"))]
        {
            std_socket.set_reuse_port(true)?;
        }

        std_socket.bind(&socket_addr.into())?;
        let tokio_socket = TokioUdpSocket::from_std(std_socket.into())?;
        Ok(tokio_socket)
    }

    /// Acquire a socket from the pool using round-robin selection.
    fn acquire(&self) -> Arc<TokioUdpSocket> {
        let idx = self.counter.fetch_add(1, AtomicOrdering::SeqCst) % self.sockets.len();
        let (_, socket) = &self.sockets[idx];
        Arc::clone(socket)
    }

    /// Acquire any socket from the pool.
    fn acquire_any(&self) -> Option<Arc<TokioUdpSocket>> {
        if self.sockets.is_empty() {
            None
        } else {
            let idx = self.counter.fetch_add(1, AtomicOrdering::SeqCst) % self.sockets.len();
            let (_, socket) = &self.sockets[idx];
            Some(Arc::clone(socket))
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();

    // Set up logging
    setup_logging(&args.log)?;

    // Parse command-line arguments
    let ips = parse_ips(&args.dip)?;
    let ports = parse_ports(&args.p)?;

    let max_num_workers = args.worker;
    let residual = Duration::from_millis(args.residual);
    let flush = args.flush;
    let use_greater_srcports = args.use_greater_srcports;
    let socket_pool_size = args.socket_pool_size;
    let trim_zeros = args.trim_zeros;
    let output_file = args.out.clone();
    let followup_payloads = args.followup_payloads;

    // Parse the bind_ip argument (can be IPv4 or IPv6)
    let bind_ip: IpAddr = args.bind_ip.parse()?;

    // Read SNI values from files or stdin
    let sni_values = read_sni_values(&args.files)?;
    let total_snis = sni_values.len();
    let processed_sni_count = Arc::new(AtomicUsize::new(0));

    // Prepare destination ports
    let mut destination_ports = ports;
    destination_ports.shuffle(&mut thread_rng());

    // Parse the source ports if provided; otherwise, generate a list.
    let source_ports = if let Some(sport_str) = args.sport {
        Some(parse_ports(&sport_str)?)
    } else {
        let start_port = 2;
        let end_port = 65534;
        let mut all_ports: Vec<u16> = (start_port..=end_port).collect();
        all_ports.shuffle(&mut thread_rng());
        let num_ports = (socket_pool_size - 1).min(all_ports.len());
        let mut src_ports: Vec<u16> = all_ports.into_iter().take(num_ports).collect();
        src_ports.push(65535);
        src_ports.shuffle(&mut thread_rng());
        Some(src_ports)
    };

    // Create channels for available ports and cooldown
    let (port_sender, port_receiver) = mpsc::unbounded_channel::<u16>();
    let (cooldown_sender, cooldown_receiver) = mpsc::unbounded_channel::<u16>();

    // Populate the available ports channel
    for port in destination_ports {
        port_sender.send(port)?;
    }

    // Share the port_receiver among workers using Arc and Mutex
    let shared_port_receiver = Arc::new(Mutex::new(port_receiver));
    let all_jobs_done = Arc::new(AtomicBool::new(false));

    // Spawn the cooldown manager task
    let cooldown_handle = {
        let port_sender = port_sender.clone();
        let all_jobs_done = Arc::clone(&all_jobs_done);
        task::spawn(async move {
            cooldown_manager(cooldown_receiver, port_sender, residual, all_jobs_done).await;
        })
    };

    // Prepare SNI queue
    let sni_queue = Arc::new(Mutex::new(VecDeque::from(sni_values)));
    let shared_ips = Arc::new(ips);

    // Set up channels for results
    let (result_sender, result_receiver) = mpsc::channel::<Vec<String>>(1000);

    // Set up CSV writer task
    let writer_handle = {
        let output_file = output_file.clone();
        let result_receiver = result_receiver;
        let flush = flush;
        task::spawn(async move {
            if let Err(e) = write_results(result_receiver, output_file, flush).await {
                error!("Failed to write results: {}", e);
            }
        })
    };

    // Initialize the socket pool using the provided bind_ip.
    let socket_pool = Arc::new(SocketPool::new(socket_pool_size, source_ports.as_ref(), bind_ip).await?);

    // Optionally print the socket pool's contents.
    // info!("Socket Pool Contents:\n{}", socket_pool.display());

    // Create a semaphore to limit the number of concurrent workers
    let semaphore = Arc::new(Semaphore::new(max_num_workers));

    // Spawn worker tasks.
    for _ in 0..max_num_workers {
        let permit = semaphore.clone().acquire_owned().await.unwrap();
        let shared_port_receiver = Arc::clone(&shared_port_receiver);
        let cooldown_sender = cooldown_sender.clone();
        let sni_queue = Arc::clone(&sni_queue);
        let shared_ips = Arc::clone(&shared_ips);
        let result_sender = result_sender.clone();
        let all_jobs_done = Arc::clone(&all_jobs_done);
        let socket_pool = Arc::clone(&socket_pool);
        let processed_sni_count = Arc::clone(&processed_sni_count);

        // Pass in the bind_ip so that ClientHello packets are generated with the proper IP family.
        let bind_ip_worker = bind_ip;
        let trim_zeros = trim_zeros;
        let use_greater_srcports = use_greater_srcports;
        let followup_payloads = followup_payloads;

        task::spawn(async move {
            worker(
                result_sender,
                shared_port_receiver,
                cooldown_sender,
                sni_queue,
                shared_ips,
                all_jobs_done,
                socket_pool,
                total_snis,
                processed_sni_count, 
                trim_zeros, 
                use_greater_srcports,
                bind_ip_worker,
                followup_payloads,  // Pass the number of followup payloads
            )
            .await;
            drop(permit);
        });
    }

    // Drop the original senders as workers have their own clones.
    drop(port_sender);
    drop(cooldown_sender);
    drop(result_sender);

    info!("All jobs have been dispatched.");

    // Wait until all SNIs have been processed.
    loop {
        {
            let sni_lock = sni_queue.lock().await;
            if sni_lock.is_empty() {
                break;
            }
        }
        sleep(Duration::from_secs(1)).await;
    }

    // Signal completion.
    all_jobs_done.store(true, AtomicOrdering::SeqCst);

    // Wait for cooldown manager and CSV writer to finish.
    cooldown_handle.await?;
    writer_handle.await?;

    info!("Finished all jobs and cooldowns. Exiting program.");

    Ok(())
}

/// Sets up logging based on user configuration.
fn setup_logging(log_file: &Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    if let Some(log_file) = log_file {
        let file = File::create(log_file)?;
        let file = Arc::new(StdMutex::new(file));
        env_logger::Builder::from_default_env()
            .format(move |_buf, record| {
                let mut file = file.lock().unwrap();
                writeln!(
                    *file,
                    "{} [{}] - {}",
                    Local::now().format("%Y-%m-%dT%H:%M:%S"),
                    record.level(),
                    record.args()
                )
            })
            .target(env_logger::Target::Stdout)
            .filter_level(LevelFilter::Info)
            .init();
    } else {
        env_logger::Builder::from_default_env()
            .format_timestamp(None)
            .filter_level(LevelFilter::Info)
            .init();
    }
    Ok(())
}

/// Writes results to CSV.
async fn write_results(
    mut result_receiver: mpsc::Receiver<Vec<String>>,
    output_file: Option<String>,
    flush: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let writer: Box<dyn Write + Send> = if let Some(output_file) = output_file {
        Box::new(File::create(output_file)?)
    } else {
        Box::new(io::stdout())
    };
    let mut csv_writer = Writer::from_writer(writer);

    // Write CSV headers.
    csv_writer.write_record(&[
        "Elapsed_Millis",
        "SNI",
        "DIP",
        "Duration_Millis",
        "Port",
    ])?;

    while let Some(result) = result_receiver.recv().await {
        csv_writer.write_record(&result)?;
        if flush {
            csv_writer.flush()?;
        }
    }
    csv_writer.flush()?;
    Ok(())
}

/// Worker function that processes SNI-port pairs.
async fn worker(
    result_sender: mpsc::Sender<Vec<String>>,
    port_receiver: Arc<Mutex<mpsc::UnboundedReceiver<u16>>>,
    cooldown_sender: UnboundedSender<u16>,
    sni_queue: Arc<Mutex<VecDeque<String>>>,
    shared_ips: Arc<Vec<IpAddr>>,
    _all_jobs_done: Arc<AtomicBool>,
    socket_pool: Arc<SocketPool>, 
    total_snis: usize,                          
    processed_sni_count: Arc<AtomicUsize>,
    trim_zeros: bool,
    use_greater_srcports: bool,
    bind_ip: IpAddr,
    num_payloads: usize,  // New parameter for the number of followup payloads
) {
    loop {
        // Fetch the next SNI value.
        let sni = {
            let mut sni_lock = sni_queue.lock().await;
            sni_lock.pop_front()
        };

        let sni = match sni {
            Some(sni) if !sni.is_empty() => sni,
            _ => break, // No more SNIs to process.
        };

        info!("Worker got the job: {}", sni);

        // Receive a destination port from the available pool.
        let port = {
            let mut port_lock = port_receiver.lock().await;
            match port_lock.recv().await {
                Some(port) => port,
                None => {
                    info!("Worker: Port channel closed. Exiting.");
                    break;
                }
            }
        };

        let start_time = Instant::now();

        // Generate a single ClientHello for this SNI and port.
        let client_hello = match generate_client_hello(&sni, trim_zeros, bind_ip) {
            Ok(ch) => ch,
            Err(e) => {
                error!("Failed to generate ClientHello for {}: {}", sni, e);
                if let Err(e) = cooldown_sender.send(port) {
                    error!("Failed to send port {} to cooldown: {}", port, e);
                }
                continue;
            }
        };

        // Acquire a socket from the pool.
        let socket = if use_greater_srcports {
            let sockets = &socket_pool.sockets;
            let idx = sockets
                .binary_search_by(|&(srcport, _)| srcport.cmp(&(port + 1)))
                .unwrap_or_else(|x| x);

            let selected_socket = if idx < sockets.len() {
                let (_srcport, sock) = &sockets[idx];
                Some(Arc::clone(sock))
            } else {
                sockets.iter()
                    .find(|&&(srcport, _)| srcport == port)
                    .map(|&(_, ref sock)| Arc::clone(sock))
            };

            if let Some(sock) = selected_socket {
                sock
            } else {
                error!("No available socket with srcport >= dstport ({})", port);
                if let Err(e) = cooldown_sender.send(port) {
                    error!("Failed to send port {} to cooldown: {}", port, e);
                }
                continue;
            }
        } else {
            match socket_pool.acquire_any() {
                Some(sock) => sock,
                None => {
                    error!("No available socket in the pool");
                    if let Err(e) = cooldown_sender.send(port) {
                        error!("Failed to send port {} to cooldown: {}", port, e);
                    }
                    continue;
                }
            }
        };

        let local_addr = socket.local_addr().unwrap_or_else(|_| SocketAddr::new(bind_ip, 0));
        let src_port = local_addr.port();
        info!("Sending packets from srcport {} to dstport {}", src_port, port);

        // Spawn tasks to send ClientHello and payloads to each DIP in parallel.
        let mut dip_handles = Vec::new();
        for &ip in shared_ips.iter() {
            let addr = SocketAddr::new(ip, port);
            let socket = Arc::clone(&socket);
            let client_hello_clone = client_hello.clone();

            let handle = task::spawn(async move {
                // Send ClientHello.
                if let Err(e) = socket.send_to(&client_hello_clone, &addr).await {
                    error!("Failed to send ClientHello to {}: {}", addr, e);
                    return;
                }
                info!("Sent ClientHello to {}", addr);

                sleep(Duration::from_secs(4)).await;
                // Send payloads with 1-second intervals.
                for i in 1..=num_payloads {
                    sleep(Duration::from_secs(1)).await;
                    let payload = format!("Payload Number: {}", i).into_bytes();
                    if let Err(e) = socket.send_to(&payload, &addr).await {
                        error!("Error sending payload {} to {}: {}", i, addr, e);
                    }
                }
                info!("Sent {} payloads to {}", num_payloads, addr);
            });
            dip_handles.push(handle);
        }

        // Wait for all DIP tasks to finish.
        for handle in dip_handles {
            if let Err(e) = handle.await {
                error!("Failed to join DIP task: {:?}", e);
            }
        }

        let end_time = Instant::now();
        let duration_millis = end_time.duration_since(start_time).as_millis();

        // Prepare the result record.
        let result = vec![
            format!("{}", start_time.elapsed().as_millis()),
            sni.clone(),
            shared_ips
                .iter()
                .map(|ip| ip.to_string())
                .collect::<Vec<String>>()
                .join(","),
            format!("{}", duration_millis),
            format!("{}", port),
        ];

        if let Err(e) = result_sender.send(result).await {
            error!("Failed to send result: {}", e);
        }
        info!(
            "Finished sending {} to all DIPs on port {} in {} ms",
            sni, port, duration_millis
        );

        // Send the port to the cooldown manager.
        if let Err(e) = cooldown_sender.send(port) {
            error!("Failed to send port {} to cooldown: {}", port, e);
        }

        let count = processed_sni_count.fetch_add(1, AtomicOrdering::SeqCst) + 1;
        info!("Processed {}/{} domains", count, total_snis);
    }
}

/// Generates a single ClientHello packet for the given SNI.
// fn generate_client_hello(sni: &str, trim_zeros: bool, bind_ip: IpAddr) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
//     let mut config = Config::new(quiche::PROTOCOL_VERSION)?;
//     config.verify_peer(false);
//     config.set_application_protos(b"\x02h3")?;

//     let scid = generate_scid();
//     let local_addr = SocketAddr::new(bind_ip, 0);

//     let mut conn = quiche::connect(Some(sni), &scid, local_addr, &mut config)?;

//     let mut out = [0; MAX_DATAGRAM_SIZE];
//     let (write, _) = conn.send(&mut out)?;

//     let packet = &out[..write];

//     if trim_zeros {
//         let trimmed_packet = trim_trailing_zeros(packet);
//         Ok(trimmed_packet.to_vec())
//     } else {
//         Ok(packet.to_vec())
//     }
// }

/// Generates a single ClientHello packet for the given SNI, padding it to 1500 bytes.
fn generate_client_hello(
    sni: &str,
    trim_zeros: bool,
    bind_ip: IpAddr,
) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    
    let mut config = Config::new(quiche::PROTOCOL_VERSION)?;

    // let mut boring_ssl_context = boring::ssl::SslContextBuilder::new(SslMethod::tls())?;

    // let curves = [SslCurve::X25519_KYBER768_DRAFT00];

    // boring_ssl_context.set_curves(&curves)?;

    // let mut config = Config::with_boring_ssl_ctx_builder(quiche::PROTOCOL_VERSION,boring_ssl_context)?;

    

    config.verify_peer(false);
    config.set_application_protos(quiche::h3::APPLICATION_PROTOCOL)?;

    
    config.set_max_recv_udp_payload_size(1200);


    let scid = generate_scid();

    config.set_max_send_udp_payload_size(1300);

    let local_addr = SocketAddr::new(bind_ip, 0);


    let url = url::Url::parse("https://cloudflare-quic.com/").unwrap();
    let peer_addr = url.socket_addrs(|| None).unwrap()[0];


    let mut conn = quiche::connect(Some(sni), &scid, local_addr, peer_addr, &mut config)?;


    // Use the pre-defined MAX_DATAGRAM_SIZE (still 1350) for the buffer.
    let mut out = [0; MAX_DATAGRAM_SIZE];
    let (write, _) = conn.send(&mut out)?;


    let packet = &out[..write];

    // Depending on the flag, either trim trailing zeros or use the packet as is.
    let mut client_hello = if trim_zeros {
        trim_trailing_zeros(packet).to_vec()
    } else {
        packet.to_vec()
    };

    



    // Pad the ClientHello to 1500 bytes if it is shorter.
    // if client_hello.len() < 1500 {
    //     client_hello.resize(1500, 0);
    // }
    info!("Client Hello Len: {}", client_hello.len());


    Ok(client_hello)
}


/// Trims trailing null bytes (zeros) from a byte slice.
fn trim_trailing_zeros(packet: &[u8]) -> &[u8] {
    let mut end = packet.len();
    while end > 0 && packet[end - 1] == 0 {
        end -= 1;
    }
    &packet[..end]
}

/// Cooldown manager with a priority queue (min-heap).
async fn cooldown_manager(
    mut cooldown_receiver: UnboundedReceiver<u16>,
    port_sender: UnboundedSender<u16>,
    residual: Duration,
    all_jobs_done: Arc<AtomicBool>,
) {
    let mut heap: BinaryHeap<CooldownPort> = BinaryHeap::new();

    loop {
        tokio::select! {
            Some(port) = cooldown_receiver.recv() => {
                let available_time = Instant::now() + residual;
                heap.push(CooldownPort { available_time, port });
                info!("Port {} entered cooldown until {:?}", port, available_time);
            },
            _ = sleep(Duration::from_millis(100)) => {
                let now = Instant::now();
                while let Some(cooldown_port) = heap.peek() {
                    if cooldown_port.available_time <= now || all_jobs_done.load(AtomicOrdering::SeqCst) {
                        let cooldown_port = heap.pop().unwrap();
                        if let Err(e) = port_sender.send(cooldown_port.port) {
                            error!("Failed to return port {} to pool: {}", cooldown_port.port, e);
                        } else {
                            info!("Cooldown complete. Port {} returned to pool.", cooldown_port.port);
                        }
                    } else {
                        break;
                    }
                }
                if all_jobs_done.load(AtomicOrdering::SeqCst) && heap.is_empty() {
                    info!("All jobs done and no ports in cooldown. Exiting cooldown manager.");
                    break;
                }
            }
        }
    }

    while let Some(cooldown_port) = heap.pop() {
        if let Err(e) = port_sender.send(cooldown_port.port) {
            error!("Failed to return port {} to pool during shutdown: {}", cooldown_port.port, e);
        } else {
            info!("Cooldown complete during shutdown. Port {} returned to pool.", cooldown_port.port);
        }
    }

    info!("Cooldown manager has finished processing all cooldowns.");
}

/// Parses a comma-separated string of IP addresses or subnets.
/// 
/// If an entry contains a "/" character, it is parsed as a subnet using the `ipnet` crate
/// and expanded into its individual IP addresses. For safety, if the subnet would result
/// in more than 4096 addresses, an error is returned.
fn parse_ips(ip_str: &str) -> Result<Vec<IpAddr>, Box<dyn std::error::Error>> {
    let mut ips = Vec::new();
    for part in ip_str.split(',') {
        let trimmed = part.trim();
        if trimmed.contains('/') {
            // Parse as a subnet.
            let net: IpNet = trimmed.parse()?;
            // Calculate the total number of addresses.
            let count = match net {
                IpNet::V4(netv4) => 2u128.pow(32 - netv4.prefix_len() as u32),
                IpNet::V6(netv6) => 2u128.pow(128 - netv6.prefix_len() as u32),
            };
            let max_allowed = 4096;
            if count > max_allowed {
                return Err(format!(
                    "Subnet {} expands to {} addresses, which exceeds the allowed maximum of {}",
                    trimmed, count, max_allowed
                )
                .into());
            }
            // Expand the subnet into individual IP addresses.
            for ip in net.hosts() {
                ips.push(ip);
            }
        } else {
            // Parse as a single IP address.
            let ip: IpAddr = trimmed.parse()?;
            ips.push(ip);
        }
    }
    Ok(ips)
}

/// Parses a comma-separated string of ports, including ranges (e.g., 10000-10010).
fn parse_ports(port_str: &str) -> Result<Vec<u16>, Box<dyn std::error::Error>> {
    let mut ports = Vec::new();
    for part in port_str.split(',') {
        let part = part.trim();
        if part.contains('-') {
            let mut range = part.split('-');
            let start: u16 = range.next().unwrap().parse()?;
            let end: u16 = range.next().unwrap().parse()?;
            for port in start..=end {
                ports.push(port);
            }
        } else {
            ports.push(part.parse()?);
        }
    }
    Ok(ports)
}

/// Reads SNI values from specified files or stdin.
fn read_sni_values(files: &Vec<String>) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    let mut sni_values = Vec::new();

    if !files.is_empty() {
        for file in files {
            if file == "-" {
                let stdin = io::stdin();
                for line in stdin.lock().lines() {
                    sni_values.push(line?);
                }
            } else {
                let f = File::open(file)?;
                let reader = BufReader::new(f);
                for line in reader.lines() {
                    sni_values.push(line?);
                }
            }
        }
    } else {
        let stdin = io::stdin();
        for line in stdin.lock().lines() {
            sni_values.push(line?);
        }
    }

    Ok(sni_values)
}

/// Generates a random Connection ID for QUIC.
fn generate_scid() -> ConnectionId<'static> {
    let mut scid = [0; 16];
    rand::thread_rng().fill_bytes(&mut scid);
    ConnectionId::from_vec(scid.to_vec())
}
