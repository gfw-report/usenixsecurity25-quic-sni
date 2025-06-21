package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	"github.com/gaukas/clienthellod"
	"github.com/google/gopacket"
	"github.com/google/gopacket/layers"
	"github.com/google/gopacket/pcap"
)

// pinfo structure to store packet information
type pinfo struct {
	srcIP      net.IP
	dstIP      net.IP
	srcPort    uint16
	dstPort    uint16
	udpPayload []byte
	servername string
	ts         time.Time // Timestamp field
	censored   bool
}

func usage() {
	fmt.Fprintf(os.Stderr, `Usage:
    %[1]s [OPTION]... [FILE]...

Description:
    This program, running on the server-side, reads in pcap files offline or captures live packets from a network interface.
	It marks a domain as blocked if the SNI is first received in a QUIC Initial packet
	but within the -timeout duration, it doesn't receive any following up UDP packets containing -magic string at the same 4-tuple.
	With no FILE, or when FILE is -, read standard input.

Examples:
    Extract the blocked domains in each pcap file under the current directory:
        %[1]s *.pcap
    Capture live packets from interface eth0:

        sudo %[1]s -i eth0

Options:
`, os.Args[0])
	flag.PrintDefaults()
}

// GetFiles return a slice of opened files.
// usage example: in external function, files := GetFiles(flag.Args())
func GetFiles(filePaths []string) []*os.File {
	files := make([]*os.File, 0)
	if len(filePaths) == 0 {
		files = append(files, os.Stdin)
	}
	for _, path := range filePaths {
		if path == "-" {
			files = append(files, os.Stdin)
		} else if strings.HasPrefix(path, "~") {
			// it's better not to expand ~, as it may not be consistent with the shell's behavior. For example,
			// sudo ./program ~/path/to/*.pcap would be expanded by shell to /home/user/path/to/*.pcap
			// sudo ./program "~/path/to/*.pcap" would be handled by this program,
			// and if we use os.USHomeDir() to replace ~, it would be expanded to /root/path/to/*.pcap
			log.Panicln("Please use absolute path instead of ~ to avoid unexpected behavior.")
		} else {
			matches, err := filepath.Glob(path)
			if err != nil {
				log.Panicln(err)
			}
			for _, p := range matches {
				file, err := os.Open(p)
				if err != nil {
					log.Panicln(err)
				}
				files = append(files, file)
			}
		}
	}

	return files
}

// ReadFiles return a channel and then sequentially pipe all lines in filePaths to the channel in a non-blocking way.
// usage example: in external function, lines := ReadFiles(flag.Args())
func ReadFiles(filePaths []string) chan string {
	const maxNumLines = 100000
	lines := make(chan string, maxNumLines)
	go func() {
		files := GetFiles(filePaths)
		for _, file := range files {
			scanner := bufio.NewScanner(file)
			// optionally, resize scanner's capacity for lines over 64K
			if err := scanner.Err(); err != nil {
				log.Panicln(err)
			}
			for scanner.Scan() {
				lines <- scanner.Text()
			}
			file.Close()
		}
		close(lines)
	}()
	return lines
}

func generateKey(srcIP, dstIP net.IP, srcPort, dstPort uint16) string {
	return fmt.Sprintf("%s:%d-%s:%d", srcIP.String(), srcPort, dstIP.String(), dstPort)
}

// Manager to handle all pinfo records
type pinfoManager struct {
	records               map[string]*pinfo
	mu                    sync.Mutex
	latestPacketTimestamp int64 // UnixNano representation of time.Time
}

func newPinfoManager() *pinfoManager {
	return &pinfoManager{
		records:               make(map[string]*pinfo),
		latestPacketTimestamp: 0,
	}
}

// Adds a pinfo to the manager
func (pm *pinfoManager) add(p *pinfo) {
	pm.mu.Lock()
	defer pm.mu.Unlock()
	key := generateKey(p.srcIP, p.dstIP, p.srcPort, p.dstPort)
	pm.records[key] = p
}

// Checks for expiration and removes expired pinfo entries
func (pm *pinfoManager) startExpiryCheck(timeout time.Duration, isStdin bool) {
	go func() {
		for {
			time.Sleep(1 * time.Second)

			var currentTime time.Time

			if isStdin {
				currentTime = time.Now()
			} else {
				currentTime = pm.getLatestPacketTimestamp()
			}

			pm.mu.Lock()
			for key, entry := range pm.records {
				if currentTime.After(entry.ts.Add(timeout)) {
					// Expired entry
					fmt.Printf("%s,%s,%s,%d,%d,%s,%t\n",
						entry.ts.Format(time.RFC3339),
						entry.srcIP.String(),
						entry.dstIP.String(),
						entry.srcPort,
						entry.dstPort,
						entry.servername,
						entry.censored,
					)
					delete(pm.records, key)
				}
			}
			pm.mu.Unlock()
		}
	}()
}

// Updates the latestPacketTimestamp atomically
func (pm *pinfoManager) updateLatestPacketTimestamp(ts time.Time) {
	unixNano := ts.UnixNano()
	for {
		current := atomic.LoadInt64(&pm.latestPacketTimestamp)
		if unixNano > current {
			if atomic.CompareAndSwapInt64(&pm.latestPacketTimestamp, current, unixNano) {
				break
			}
		} else {
			break
		}
	}
}

func (pm *pinfoManager) flushAll() {
	pm.mu.Lock()
	defer pm.mu.Unlock()
	for key, entry := range pm.records {
		// Output the entry in CSV format
		fmt.Printf("%s,%s,%s,%d,%d,%s,%t\n",
			entry.ts.Format(time.RFC3339),
			entry.srcIP.String(),
			entry.dstIP.String(),
			entry.srcPort,
			entry.dstPort,
			entry.servername,
			entry.censored,
		)
		// Remove the entry from the records map
		delete(pm.records, key)
	}
}

// Retrieves the latestPacketTimestamp as time.Time
func (pm *pinfoManager) getLatestPacketTimestamp() time.Time {
	unixNano := atomic.LoadInt64(&pm.latestPacketTimestamp)
	if unixNano == 0 {
		return time.Time{}
	}
	return time.Unix(0, unixNano)
}

// Checks if the magic string is found in the packet payload
func containsMagic(udpPayload []byte, magic string) bool {

	if len(udpPayload) < 20 {
		return true
	}

	return false
	// return len(udpPayload) >= len(magic) && string(udpPayload[:len(magic)]) == magic
}

// Extracts SNI (Server Name) from the QUIC Initial packet
func extractSNI(packet gopacket.Packet) (string, error) {
	udpLayer := packet.Layer(layers.LayerTypeUDP)
	if udpLayer == nil {
		return "", fmt.Errorf("no UDP layer found")
	}
	udp, _ := udpLayer.(*layers.UDP)
	raw := udp.Payload

	// Try to unmarshal the QUIC ClientHello
	cip, err := clienthellod.ParseQUICCIP(raw)
	if err != nil {
		return "", fmt.Errorf("failed to parse QUIC ClientHello: %v", err)
	}

	return cip.QCH.ClientHello.ServerName, nil
}

func gotMagic(key string, manager *pinfoManager) {
	// if the key is found in the records, mark the domain as not blocked
	manager.mu.Lock()
	existing, found := manager.records[key]
	manager.mu.Unlock()

	if found {
		existing.censored = false
		// Print the entry before removing it
		// output a CSV with the following fields: timestamp, srcIP, dstIP, srcPort, dstPort, servername, censored
		fmt.Printf("%s,%s,%s,%d,%d,%s,%t\n",
			existing.ts.Format(time.RFC3339),
			existing.srcIP.String(),
			existing.dstIP.String(),
			existing.srcPort,
			existing.dstPort,
			existing.servername,
			existing.censored,
		)

		// Remove the entry
		manager.mu.Lock()
		delete(manager.records, key)
		manager.mu.Unlock()
	}

	// if not found, which is very common when more than one Magic packet is sent, do nothing
}

// Get the necessary packet details
func parsePacket(packet gopacket.Packet, manager *pinfoManager, magic *string) error {
	ipLayer := packet.Layer(layers.LayerTypeIPv4)
	if ipLayer == nil {
		return fmt.Errorf("no IPv4 layer found")
	}
	ip, _ := ipLayer.(*layers.IPv4)

	udpLayer := packet.Layer(layers.LayerTypeUDP)
	if udpLayer == nil {
		return fmt.Errorf("no UDP layer found")
	}
	udp, _ := udpLayer.(*layers.UDP)

	key := generateKey(ip.SrcIP, ip.DstIP, uint16(udp.SrcPort), uint16(udp.DstPort))

	// Update latestPacketTimestamp with the packet's timestamp
	manager.updateLatestPacketTimestamp(packet.Metadata().Timestamp)

	if containsMagic(udp.Payload, *magic) {
		// if it's a magic packet
		gotMagic(key, manager)
		return nil
	}

	// Extract SNI if it's a QUIC Initial packet
	sni, err := extractSNI(packet)
	if err != nil || sni == "" {
		return fmt.Errorf("failed to extract SNI or no SNI value: %v, %v", err, sni)
	}

	// if it's a magic packet, update the entry if it exists, or add a new entry
	manager.mu.Lock()
	_, found := manager.records[key]
	manager.mu.Unlock()

	pinfoEntry := &pinfo{
		srcIP:      ip.SrcIP,
		dstIP:      ip.DstIP,
		srcPort:    uint16(udp.SrcPort),
		dstPort:    uint16(udp.DstPort),
		udpPayload: udp.Payload,
		servername: sni,
		ts:         packet.Metadata().Timestamp,
		censored:   true,
	}

	if found { // if this is a new QUIC Initial packet, add it to the manager
		// This is a new QUIC Initial packet with the same 4-tuple,
		// update the entry by deleting the old one and adding the new one.
		// This happens when the client sends more than one QUIC Initial packet with the same 4-tuple in a short period of time.
		manager.mu.Lock()
		manager.records[key] = pinfoEntry
		manager.mu.Unlock()
	} else {
		manager.add(pinfoEntry)
	}

	return nil
}

func main() {
	flag.Usage = usage
	filter := flag.String("filter", "udp", "BPF filter syntax.")
	timeout := flag.Duration("timeout", 10*time.Second, "timeout duration (e.g., 10s, 1m)")
	magic := flag.String("magic", "Payload", "magic string to confirm the reachability from the client.")
	iface := flag.String("i", "", "interface to capture live packets")
	flag.Parse()

	var isStdin bool
	// Check if we're reading from stdin
	if len(flag.Args()) == 0 || flag.Args()[0] == "-" {
		isStdin = true
	}

	manager := newPinfoManager()
	manager.startExpiryCheck(*timeout, isStdin)

	// Set up a channel to listen for interrupt signals (e.g., Ctrl+C)
	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)

	var wg sync.WaitGroup
	wg.Add(1)

	go func() {

		defer wg.Done()

		if *iface != "" {
			// Live capture
			handle, err := pcap.OpenLive(*iface, 262144, true, pcap.BlockForever)
			if err != nil {
				log.Fatalf("Error opening device %s: %v", *iface, err)
			}
			defer handle.Close()

			err = handle.SetBPFFilter(*filter)
			if err != nil {
				log.Panicln("Failed to set BPFFilter:", err)
			}

			packetSource := gopacket.NewPacketSource(handle, handle.LinkType())
			packetChan := make(chan gopacket.Packet, 1000000) // Buffered channel

			// Start worker goroutines
			numWorkers := runtime.NumCPU() * 4 // Adjust based on your CPU cores
			for i := 0; i < numWorkers; i++ {
				go func() {
					for packet := range packetChan {
						err := parsePacket(packet, manager, magic)
						if err != nil {
							// Consider logging to a buffered channel instead
						}
					}
				}()
			}

			// Read packets and send them to the channel
			for packet := range packetSource.Packets() {
				packetChan <- packet
			}

			close(packetChan)

		} else {

			// Read from files
			// Read the files from the arguments using readfiles package
			files := GetFiles(flag.Args())

			for _, file := range files {
				filename := file.Name()

				log.Println("Started parsing:", filename)

				handle, err := pcap.OpenOfflineFile(file)
				if err != nil {
					log.Println("Failed to open pcap file:", err)
					continue
				}
				defer handle.Close()

				err = handle.SetBPFFilter(*filter)
				if err != nil {
					log.Panicln("Failed to set BPFFilter:", err)
				}

				// Use the handle as a packet source to process all packets
				packetSource := gopacket.NewPacketSource(handle, handle.LinkType())
				packetChan := packetSource.Packets()

			PacketLoop:
				for {
					select {
					case packet, ok := <-packetChan:

						if !ok {
							// End of packet source
							// log.Println("EOFFFFF:", err)
							break PacketLoop
						}
						err := parsePacket(packet, manager, magic)
						if err != nil {
							log.Println("Failed to parse packet:", err)
						}
					case <-sigs:
						log.Println("Termination signal received. Flushing remaining entries.")
						handle.Close()
						manager.flushAll()
						return
					}
				}

			}

			manager.flushAll()

			log.Println("Finished parsing all files.")
		}
	}()

	wg.Wait()

}
