import socket
import time
import random

# Configuration
TARGET_IP = "US_SERVER_IP"  
DEST_PORT = 53  
SOURCE_PORT = 0  
SPECIAL_PAYLOAD = bytes.fromhex("c700000001109422a1011be01c6cfd6d44976055fa2510a8020f889ec01bff5a1d9dc4de861de30040e1662953d714d04f7d383cc874ea1e268287c0de7e17ed99ff64900b9e14af6d32f4e4e74339ead6d8fa54c77b928e0907c46cb76c6c960b9e3b5c71bbdccb1e6b349bc25031fc46e07a36789d456e35347d71eb243fc70233e9885ac46bf92828cbc59bda247335890b9e12262cc73f92a37e5149c741264307870860e6fed1212faa82ad0e2996c0739eff8b8535719f013407566ea1ca450003fe8da6327ebd9b9a218635bc644049b189b0422944ac35511e69b85a08de735a55383aaa1ebc9efdcbb6866c8d70c8940ca7daec9f7e502ceedfd6d8d804a931b2ee3b443af579")
EXPERIMENT_REPEATS = 20  
FOLLOWUP_COUNT = 100  


def send_packet(sock, payload, ttl, target_ip, dest_port):
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        sock.sendto(payload, (target_ip, dest_port))
    except Exception as e:
        print(f"Error sending packet: {e}")


def run_experiment(ttl):
    FOLLOWUP_PAYLOAD = bytes(f"Experiment {ttl}", encoding='utf-8')
    try:
        
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            for _ in range(1, 10):
                send_packet(sock, SPECIAL_PAYLOAD, ttl, TARGET_IP, DEST_PORT)
            time.sleep(5)
            
            for _ in range(FOLLOWUP_COUNT):
                send_packet(sock, FOLLOWUP_PAYLOAD, 64, TARGET_IP, DEST_PORT)

    except Exception as e:
        print(f"Error during experiment {experiment + 1}: {e}")


if __name__ == "__main__":
    for i in range(EXPERIMENT_REPEATS):
        print(f"Starting experiment {i + 1}/{EXPERIMENT_REPEATS}")
        run_experiment(ttl=i+1)
