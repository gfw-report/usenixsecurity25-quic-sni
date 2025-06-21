import socket
import sys
from time import sleep

def send_packets(server_ip, server_port, payload_file, packet_count, wait):
    try:
        # Load binary payload
        with open(payload_file, 'rb') as file:
            payload = file.read()

        print(f"Sending {packet_count} packets to {server_ip}...")
        for _ in range(packet_count):
            # Create a UDP socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client_socket.sendto(payload, (server_ip, server_port))
            print(f"Sent packet from {client_socket.getsockname()[0]}:{client_socket.getsockname()[1]} to {server_ip}:{server_port}.")
            sleep(wait)

        print(f"Successfully sent {packet_count} packets.")
        client_socket.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python client.py <server_ip> <server_port> <payload_file> <packet_count> <wait>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    payload_file = sys.argv[3]
    packet_count = int(sys.argv[4])
    wait = int(sys.argv[5])

    send_packets(server_ip, server_port, payload_file, packet_count, wait)
