package main

import (
	"flag"
	"fmt"
	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"golang.org/x/net/ipv4"
	"os"
	"strings"
	"log"
	"net"
	"encoding/hex"
	"strconv"
    	"sync"
	"time"
	"bufio"
)

func send(fromip net.IP, toip net.IP, rawConn *ipv4.RawConn, quic_payload []byte, srcport int, dstport int) {

	srcip := fromip
	dstip := toip
	dport := layers.UDPPort(dstport)
	sport := layers.UDPPort(srcport)

	ip4 := layers.IPv4{
		SrcIP:    srcip,
		DstIP:    dstip,
		Version:  4,
		TTL:      64,
		Protocol: layers.IPProtocolUDP,
	}

	udp_payload := layers.UDP{
		SrcPort: sport,
		DstPort: dport,
	}
	opts := gopacket.SerializeOptions{
		FixLengths:       true,
		ComputeChecksums: true,
	}

	udp_payload.SetNetworkLayerForChecksum(&ip4)

	ipHeaderBuf := gopacket.NewSerializeBuffer()
	err := ip4.SerializeTo(ipHeaderBuf, opts)
	if err != nil {
		panic(err)
	}

	ipHeader, err := ipv4.ParseHeader(ipHeaderBuf.Bytes())
	if err != nil {
		panic(err)
	}

	udpPayloadBuf := gopacket.NewSerializeBuffer()

	var payload gopacket.Payload

	payload = gopacket.Payload(quic_payload)
		
	err = gopacket.SerializeLayers(udpPayloadBuf, opts, &udp_payload, payload)

	if err != nil {
		panic(err)
	}

	err = rawConn.WriteTo(ipHeader, udpPayloadBuf.Bytes(), nil)

	if err != nil {
		panic(err)
	}
}

type portPair struct {
	dport int
	sport int
}

func worker(id int, fromIp net.IP, toIp net.IP, rawConn *ipv4.RawConn,
	    quicPayload []byte, randPayload []byte, ports <-chan portPair,
    	    sleep_quic int, sleep_data int, n_data_pkts int) {

	for port := range ports {
		// QUIC client Initial
		send(fromIp, toIp, rawConn, quicPayload, port.sport, port.dport)
		if (sleep_quic != 0) {
			time.Sleep(time.Duration(sleep_quic) * time.Microsecond)
		}

		// Data packets
		for j := 0; j < n_data_pkts; j++ {
			send(fromIp, toIp, rawConn, randPayload, port.sport, port.dport)
			if (sleep_data != 0) {
				time.Sleep(time.Duration(sleep_data) * time.Microsecond)
			}
		}
	}
}

func main() {
	
	var src_ip = flag.String("src", "", "ip local to machine")
	var vp_ip = flag.String("vp", "", "ip of the controlled vantage point")
	/*
	var dst_port = flag.Int("dstport", -1, "dstport for the probes to the controlled vp (srcport will be dstport+1)")
	var sleep = flag.Int("sleep", 10, "sleep time (in microseconds) between packets")
	var limit = flag.Int("limit", -1, "number of sent packets after which we test the persistence of risidual censorship")
	var test_probes = flag.Int("test-probes", 10, "number of date packets to send to test continuity of residual censorship")
	var base_net = flag.String("base-net", "", "network ip of a /16 to send probes to")
	var cool_down = flag.Int("cool", 5, "sleep time (in seconds) between probes to the larger network and the controlled vp")
	var ticks = flag.Int("ticks", -1, "frequency of sending the probes to the controlled vp (ms)")
	var tick_sleep = flag.Int("tick-sleep", 0, "sleep time (in ms) between frequent ticks")
	*/
	var quicPayload = flag.String("payload", "c500000001108144962187fccea82488d99a65bb901e107bcbc370f1173b1983705b16cb2417d70040e1ed2f311bcfba704fe886c7c9c1332fb7a803cec479e5be90a2178c3cbef7de2cee8d67775520c938e2cd048830858fa9b5bdae17332de69ab5a23aa355b19f5066e593d38e13fb5cc6304a2439f671f61585fe8c4f4646f41c5b0b1a9867bbc77d7cbb55fba3404a56fef53d7e4fc55effca07fe3a040c6c3652c198edab6d37ecc099f433e79b8bd538bf6074f405f0565a71149f4713be781ca076fbef560408e7857c02efbb1b79321b81467db45e0ae04e9ed04e269d7f6781ceb0661927234be9ada7853dde9299a4ebf790ffa3c8c5f4cbb8a515222199d66fd6699c76ef", "QUIC paylaod to send")
	var randPayload = flag.String("rand-payload", "94b2dc28760608936eeefec1f4c76ca7b81f4eeadc23b93ad31314e25fc737a06e41ed2fa385324ad53df2376369abdda7be7ceba1e01cfb8c18ad25c8cea9ae202e003093665a6a66da02889b54a11bee9c3dd0edb6a7896bbc055341c764e084a0245014beea5b20a682ab344c30d7d7a855e3c8a958527ce2f6c4f4b4120b74d2b68cd17d1f34ff4ae986fc7da635420fb7ba1a311c40d2ecb690d07514401c7acff7c9efa0cfe3f127c9fe2c22053cba17271a10e84ad5450300b997f4281e647a95334578f1159d58921125d8cd654d8481cc13c89009281ecd5a2e4eff0cd0707320f025a9c7efc63dbd2c4e8412dce19d6274b451130d349318708899506c501a95c11e867fb9213f5b1055ebc7a7e71f015b00e235ba0e11a8b3b067255ddf151df5922ef25ba609555071ec0b48260548a42ad0f507fb9596a22a278d372052f7d4d6ddba39064982ffd45c753e0b8abcfef2f2088501df5b9e77f9a07e61aad2bc097f1888287f9f32b923081d4d3b816523d3fdcf29968991d0174229ca37a19f7952d72c07df3c3e9105aa0ab00a6a117ad3c51d0a3ab8fc7714b020542ada7ee024c040819f3306741b7718de5251fb57564f6b4aab306a214ad5ad278ea4ce555da75816065c7059ef3e8e135f845a112b8ff028f8495a0575c3c1708f9c1e61aaf0da6fee2946ea8fe7f1c5c0439007997307477b3c75f3070bbf3ab02243e9364af02a9dcd7e22722c434f0398a0046f4893f3075768ad213f8e0ca293f38ebd031ef97352e6ffdc3bbcac30b5899300d2671257156aa1e007a5541f53a6d6e1fc046548b9eab78e9979ad504267efeaa93fe91bce81838335ff6306f6c316fab1826a107f7f91210e86f467fedfff094a5dc2efdddbb72069a23e6ce5c74d4fa6ca2efaba4be55b5eb4550c3b19eb99591bafbf474971c938204ca9aa1b1975c4ee91ba8bee37747cc64451407670d9c57d4e7c416cc30ff3e063f6efd822fcafdc3d317210979569cbfefa2fedbc2c74a8dd1903c8ffef6c1bb9605e91e4f738550b9df2414f8351e8132b2314959cc5bdfb20a0d482cadb15465ae2128aeed4bace1ea77466d4849d4022ef2c5509964ce5c420df90a16b3ccdc1ccae56ff53c6345fba30b0fdd5e2c5e6494889263a1615cdb9db4cde6d9c872872fe9c5e0fdd76af9e9019f324d0d067b08e75d571a9b037298660b17b7c1e6a3de34a8dcd1df8150df5167e4997c2b896f69434951d0d61a77b3f315b3a53beaad57f66f590e3d99504235c52fe3b4b746911a231723ec69b4871019aef1b0614c74043233ec6bc323a0c43df931eddc9f0db9e4176e5efa56abc0cafd1c5aa4f45d6cde8dfcdeaf024fea6bcd7820646f24bfa7fd9b1d283ea02a556326fc7b0d4b2a5b5be6e522ce2f2d3b39f3281be112d6ae74fa042b4727bc6b23f100873dd3150dee8c0e97dc191c76e811c1addd74c616713c8c8aac11a015afbb7f806528e3add8166db929d36617f73379fec87033e23ba4b7ce216b739b73a60387c5d26d9259c9dd1b133da8de529344ec59af2", "random data to send after QUIC payload")
	var sleep_quic = flag.Int("sleep-quic", 100, "sleep time (in microseconds) between the first QUIC packet and the remaining data packets")
	var sleep_data = flag.Int("sleep-data", 100, "sleep time (in microseconds) between data packets")
	var n_data_pkts = flag.Int("num-data-pkts", 3, "number of data packets to send after QUIC payload 'payload'")
	var nworkers = flag.Int("workers", 100, "number of threads during a simultaneous test")
	var fports = flag.String("ports", "", "Filename for list of src dest ports (space-separated pair per line)")

	flag.Parse()

	var packetConn net.PacketConn
	var rawConn *ipv4.RawConn
	packetConn, err := net.ListenPacket("ip4:udp", *src_ip)
	if err != nil {
		panic(err)
	}
	rawConn, err = ipv4.NewRawConn(packetConn)
	if err != nil {
		panic(err)
	}

	quicDecoded, err := hex.DecodeString(*quicPayload)
	if err != nil {
		log.Fatal(err)
	}

	randDecoded, err := hex.DecodeString(*randPayload)
	if err != nil {
                log.Fatal(err)
        }

	srcIP := net.ParseIP(*src_ip).To4()
	if srcIP == nil {
                fmt.Println("srcIP: Invalid IPv4 address")
                return
        }

	vpIP := net.ParseIP(*vp_ip).To4()
        if vpIP == nil {
                fmt.Println("vpIP: Invalid IPv4 address")
                return
        }

	// Jobs channel
	ports := make(chan portPair, *nworkers)

	// Workers
	var wg sync.WaitGroup
	for i := range(*nworkers) {
		wg.Add(1)
		go func() {
			defer wg.Done()
			worker(i, srcIP, vpIP, rawConn, quicDecoded, randDecoded, ports,
				*sleep_quic, *sleep_data, *n_data_pkts)
		}()
	}


	// Read src/dst ports from file
    	file, err := os.Open(*fports)
    	if err != nil {
		fmt.Printf("Error opening file: %v\n", err)
		return
    	}
    	defer file.Close()

	scanner := bufio.NewScanner(file)
    	for scanner.Scan() {
		parts := strings.Fields(scanner.Text())
		sport, err := strconv.Atoi(parts[0])
		if (err != nil) {
			fmt.Printf("Error: not a port: %s\n", scanner.Text())
			return
		}
		dport, err := strconv.Atoi(parts[1])
		if (err != nil) {
			fmt.Printf("Error: not a port: %s\n", scanner.Text())
			return
		}
		pp := portPair{sport: sport, dport: dport}
		ports <- pp
    	}
	close(ports)

    	if err := scanner.Err(); err != nil {
		fmt.Printf("Error reading file: %v\n", err)
		return
	}


	wg.Wait()

	/*
	baseNetIP := net.ParseIP(*base_net).To4()
	if baseNetIP == nil {
		fmt.Println("baseNetIP: Invalid IPv4 address")
		return
	}
	
	var initDstportVP int
	if *dst_port == -1 {
		rand.Seed(time.Now().UnixNano())
		initDstportVP = rand.Intn(65533) + 1 // (+1) to overcome having 0 as the returned random number
	} else {
		initDstportVP = *dst_port
	}
	send(srcIP, vpIP, rawConn, quicDecoded, initDstportVP, initDstportVP+1)
	time.Sleep(time.Duration(1) * time.Second) // to ensure delivery before the storm of packets starts
	
	if *ticks > 0 {
		ticker := time.NewTicker(time.Duration(*ticks) * time.Millisecond)
		go func() {
			for range ticker.C {
				if (*tick_sleep) != 0 {
					time.Sleep(time.Duration(*tick_sleep) * time.Millisecond) // to ensure delivery before the proceeding data packets are sent
				}
				send(srcIP, vpIP, rawConn, randDecoded, initDstportVP, initDstportVP+1)
			}
		}()
	}
	for k := 1; k <= 65534; k++ {
		for i := 0; i < 256; i++ {
			for j := 0; j < 256; j++ {
				dstIP := net.IPv4(baseNetIP[0], baseNetIP[1], byte(i), byte(j))
				if (*sleep) != 0 {
					time.Sleep(time.Duration(*sleep) * time.Microsecond)
				}
				send(srcIP, dstIP, rawConn, quicDecoded, k, k+1)

				counter++
				if *limit != -1 && counter % *limit == 0 {
					if (*cool_down) != 0 {
						time.Sleep(time.Duration(*cool_down) * time.Second)
					}
					for l := 0; l < *test_probes; l++ {
						send(srcIP, vpIP, rawConn, randDecoded, initDstportVP, initDstportVP+1)
					}
					time.Sleep(time.Duration(1) * time.Second) // to ensure delivery before the storm of packets continues
				}
			}
		}
	}
	*/
}
