import socket
import struct
import time

# Configuration
TARGET_IP = "US_SERVER_IP"  
DEST_PORT = 53  
DNS_QUERY = b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01"  # DNS query for google.com
MAX_TTL = 64 
TIMEOUT = 5  


def send_dns_request(sock, ttl, target_ip, dest_port):
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
    sock.sendto(DNS_QUERY, (target_ip, dest_port))

def listen_for_response(sock):
    sock.settimeout(TIMEOUT)
    try:
        data, _ = sock.recvfrom(512)
        return data
    except socket.timeout:
        return None


def run_dns_probe():
    for ttl in range(1, MAX_TTL + 1):
        print(f"Sending DNS query with TTL={ttl}")

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                send_dns_request(sock, ttl, TARGET_IP, DEST_PORT)

                response = listen_for_response(sock)

                if response:
                    print(f"Received DNS response with TTL={ttl}")
                    print(f"Response: {response.hex()}")
                    break

        except Exception as e:
            print(f"Error with TTL={ttl}: {e}")


if __name__ == "__main__":
    run_dns_probe()
