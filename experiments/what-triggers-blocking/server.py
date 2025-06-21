import socket
import sys
import threading

# Asynchronous server I wrote because I thought I needed it
# I don't but its here for reference
# Runner code if it is ever needed:
    # bind_ports = [base_bind_port + i * increment for i in range(packet_count)]
    # curr_timeout = timeout
    # for bind_port in bind_ports:
    #     thread = threading.Thread(target=start_server, args=(bind_ip, bind_port, curr_timeout, expected_payload))
    #     thread.start()
    #     curr_timeout += wait
# def start_server(bind_ip, bind_port, timeout, expected_payload):
#     try:
#         # Create a UDP socket
#         server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         server_socket.settimeout(timeout)
#         server_socket.bind((bind_ip, bind_port))
#         print(f"Listening on {bind_ip}:{bind_port}...")
#         data, addr = server_socket.recvfrom(65535)  # Receive a packet
#         if data == expected_payload:
#             print(f"{bind_ip}:{bind_port} received valid packet.")
#         else:
#             print(f"{bind_ip}:{bind_port} received invalid packet.")
#         server_socket.close()
#     except Exception as e:
#         print(f"{bind_ip}:{bind_port} an error occurred: {e}")

def receive_packets(bind_ip, bind_port, expected_payload_file, packet_count, timeout):
    try:
        # Load the expected payload
        with open(expected_payload_file, 'rb') as file:
            expected_payload = file.read()

        # Create a UDP socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.settimeout(timeout)
        server_socket.bind((bind_ip, bind_port))
        print(f"Listening on {bind_ip}:{bind_port}...")

        received_count = 0
        while True:
            data, addr = server_socket.recvfrom(65535)  # Receive a packet
            if data == expected_payload:
                received_count += 1
                print(f"{bind_ip}:{bind_port} received valid packet from {addr[0]}:{addr[1]}.")
            else:
                print(f"{bind_ip}:{bind_port} received invalid packet from {addr}.")
            if received_count == packet_count:
                print(f"Succesfully received {packet_count} packets.")
                break

        server_socket.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python server.py <bind_ip> <bind_port> <expected_payload_file> <packet_count> <timeout>")
        sys.exit(1)

    bind_ip = sys.argv[1]
    bind_port = int(sys.argv[2])
    expected_payload_file = sys.argv[3]
    packet_count = int(sys.argv[4])
    timeout = int(sys.argv[5])

    receive_packets(bind_ip, bind_port, expected_payload_file, packet_count, timeout)

