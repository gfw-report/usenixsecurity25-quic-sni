from scapy.all import *
import argparse
import sys

#quic_payload_to_look_for = "c500000001108144962187fccea82488d99a65bb901e107bcbc370f1173b1983705b16cb2417d70040e1ed2f311bcfba704fe886c7c9c1332fb7a803cec479e5be90a2178c3cbef7de2cee8d67775520c938e2cd048830858fa9b5bdae17332de69ab5a23aa355b19f5066e593d38e13fb5cc6304a2439f671f61585fe8c4f4646f41c5b0b1a9867bbc77d7cbb55fba3404a56fef53d7e4fc55effca07fe3a040c6c3652c198edab6d37ecc099f433e79b8bd538bf6074f405f0565a71149f4713be781ca076fbef560408e7857c02efbb1b79321b81467db45e0ae04e9ed04e269d7f6781ceb0661927234be9ada7853dde9299a4ebf790ffa3c8c5f4cbb8a515222199d66fd6699c76ef"

class Conn():
    def __init__(self, srcIP, dstIP, srcPort, dstPort, payload):
        self.srcIP = srcIP
        self.srcPort = srcPort
        self.dstIP = dstIP
        self.dstPort = dstPort
        self.id = self.srcIP + '-' + str(self.srcPort) + '-' + self.dstIP + '-' + str(self.dstPort)
        self.seen_quic = self.check_quic(payload)
        self.nb_pkts = 1

    def check_quic(self, payload):
        if bytes(payload).hex() == quic_payload_to_look_for:
            return True
        else:
            return False

def process(args):
    conns = {}
    global quic_payload_to_look_for
    quic_payload_to_look_for = args["payload"]

    for pkt in PcapReader(args["file"]):
        if pkt.haslayer(IP) and pkt.haslayer(UDP):
            if pkt[IP].dst == args["dstIP"] and pkt[IP].src == args["srcIP"]:
                # Make sure the QUIC payload sent is received and intact
                conn = Conn(pkt[IP].src, pkt[IP].dst, pkt[UDP].sport, pkt[UDP].dport, pkt[UDP].payload)
                if conn.id in conns:
                    conns[conn.id].nb_pkts += 1
                    if conns[conn.id].check_quic(pkt[UDP].payload):
                        conns[conn.id].seen_quic = True
                else:
                    conns[conn.id] = conn

    for conn in conns:
        print(conns[conn].id, conns[conn].nb_pkts, conns[conn].seen_quic)

def get_args():
    """
    Parses args
    """
    parser = argparse.ArgumentParser(description='Print number of packets received per QUIC connection give a pcap file')
    parser.add_argument('-f', '--file', action='store', required=True)
    parser.add_argument('-s', '--srcIP', action='store', required=True)
    parser.add_argument('-d', '--dstIP', action='store', required=True)
    parser.add_argument('-p', '--payload', action='store', required=True)
#'c500000001108144962187fccea82488d99a65bb901e107bcbc370f1173b1983705b16cb2417d70040e1ed2f311bcfba704fe886c7c9c1332fb7a803cec479e5be90a2178c3cbef7de2cee8d67775520c938e2cd048830858fa9b5bdae17332de69ab5a23aa355b19f5066e593d38e13fb5cc6304a2439f671f61585fe8c4f4646f41c5b0b1a9867bbc77d7cbb55fba3404a56fef53d7e4fc55effca07fe3a040c6c3652c198edab6d37ecc099f433e79b8bd538bf6074f405f0565a71149f4713be781ca076fbef560408e7857c02efbb1b79321b81467db45e0ae04e9ed04e269d7f6781ceb0661927234be9ada7853dde9299a4ebf790ffa3c8c5f4cbb8a515222199d66fd6699c76ef'
    return parser.parse_args()


def main():
    process(vars(get_args()))

if __name__ == "__main__":
    main()
