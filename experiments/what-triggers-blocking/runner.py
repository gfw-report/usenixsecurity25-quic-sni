import paramiko
import csv
import threading
from time import sleep

def execute_command(ssh_client, command):
    """Executes a command on the SSH client."""
    stdin, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode()
    error = stderr.read().decode()
    return output, error

def deploy_scripts(ssh_client, local_script, remote_path):
    """Uploads a script to the remote server."""
    sftp = ssh_client.open_sftp()
    sftp.put(local_script, remote_path)
    sftp.close()

def process_host_csv(file_path):
    """Reads a CSV file and returns a list of server details."""
    servers = []
    with open(file_path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            if len(row) == 5:
                servers.append({
                    'host': row[0],
                    'user': row[1],
                    'key': row[2],
                    'proxy_host': row[3],
                    'proxy_user': row[4],
                })
            elif len(row) == 3:
                servers.append({
                    'host': row[0],
                    'user': row[1],
                    'key': row[2],
                    'proxy_host': None,
                    'proxy_user': None,
                })
            else:
                print("Invalid row in CSV file:", row)
    return servers

def connect_to_server(server):
    """Connects to a server using SSH."""
    print(f"Connecting to {server['host']}...")
    if server['proxy_host']:
        proxy = paramiko.SSHClient()
        proxy.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        proxy.connect(hostname=server['proxy_host'], username=server['proxy_user'], key_filename=server['key'])
        transport = proxy.get_transport()
        channel = transport.open_channel("direct-tcpip", (server['host'], 22), ('', 0))
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=server['host'], username=server['user'], key_filename=server['key'], sock=channel)
    else:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=server['host'], username=server['user'], key_filename=server['key'])
    return client

def process_payloads_file(file_path):
    """Reads a CSV file and returns a list of payload files."""
    payloads = []
    with open(file_path, 'r') as file:
        for row in file:
            payloads.append(row.strip())
    return payloads

def run_server(dst_client, dst_port, packet_count, timeout, results):
    try:
        # Start server script
        server_command = f"python3 /tmp/server.py 0.0.0.0 {dst_port} /tmp/payload.bin {packet_count} {timeout}"
        print(f"Starting server script: {server_command}")
        stdout, stderr = execute_command(dst_client, server_command)

        results['server_stdout'] = stdout
        results['server_stderr'] = stderr

        # Close server connection
        dst_client.close()
        print("Server script finished.")

    except Exception as e:
        results['server_error'] = str(e)

def run_client(src_client, dst_host, dst_port, packet_count, wait, results):
    try:
        # Start client script
        client_command = f"python3 /tmp/client.py {dst_host} {dst_port} /tmp/payload.bin {packet_count} {wait}"
        print(f"Starting client script: {client_command}")
        stdout, stderr = execute_command(src_client, client_command)

        results['client_stdout'] = stdout
        results['client_stderr'] = stderr

        # Close client connection
        src_client.close()
        print("Client script finished.")

    except Exception as e:
        results['client_error'] = str(e)

def run_experiment(src_server, dst_server, payload_file, packet_count, wait, dst_port, server_timeout):
    """Runs the client-server experiment via SSH for a specified number of iterations."""
    try:
        dst_client = connect_to_server(dst_server)
        # Deploy server script
        deploy_scripts(dst_client, payload_file, "/tmp/payload.bin")

        src_client = connect_to_server(src_server)
        # Deploy client script and payload
        deploy_scripts(src_client, payload_file, "/tmp/payload.bin")

        results = {}

        # Run server and client in parallel
        server_thread = threading.Thread(target=run_server, args=(dst_client, dst_port, packet_count, server_timeout, results))
        client_thread = threading.Thread(target=run_client, args=(src_client, dst_server['host'], dst_port, packet_count, wait, results))

        server_thread.start()
        sleep(1)  # Wait for server to start
        client_thread.start()

        server_thread.join()
        client_thread.join()

        # Log output from both client and server
        print(f"\n--- Results ---")
        print("Client Output:")
        print(results.get('client_stdout', 'No Output'))
        print("Client Errors:")
        print(results.get('client_stderr', 'No Errors'))
        print("Server Output:")
        print(results.get('server_stdout', 'No Output'))
        print("Server Errors:")
        print(results.get('server_stderr', 'No Errors'))

        if 'client_error' in results:
            print("Client Error:", results['client_error'])
        if 'server_error' in results:
            print("Server Error:", results['server_error'])
        
        
        received = results.get('server_stdout', '').count("received valid packet")
        error = False
        if 'client_error' in results or 'server_error' in results:
            error = True
        if "An error occurred:" in results.get('client_stdout', '') or "an error occurred:" in results.get('server_stdout', ''):
            error = True
        return f"{src_server['host']},{dst_server['host']},{payload},{packet_count},{wait},{dst_port},{server_timeout},{received},{error}"

    except Exception as e:
        print(f"An error occurred: {e}")
        return f"{src_server['host']},{dst_server['host']},{payload},{packet_count},{wait},{dst_port},{server_timeout},0,True"

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 8:
        print("Usage: python runner.py <inside_file> <outside_file> <payloads_file> <packet_count> <wait> <server_timeout> <results_file>")
        sys.exit(1)

    inside_file = sys.argv[1]
    outside_file = sys.argv[2]
    payloads_file = sys.argv[3]
    packet_count = int(sys.argv[4])
    wait = int(sys.argv[5])
    server_timeout = int(sys.argv[6])
    results_file = sys.argv[7]

    # Process source and destination CSV files
    inside_servers = process_host_csv(inside_file)
    outside_servers = process_host_csv(outside_file)
    # Process payload files
    payloads = process_payloads_file(payloads_file)

    results_file = open(results_file, 'w')
    results_file.write("src,dst,payload,packet_count,wait,dst_port,server_timeout,packets_received,error\n")

    print("Testing inside servers...")
    for server in inside_servers:
        server = connect_to_server(server)
        deploy_scripts(server, "server.py", "/tmp/server.py")
        deploy_scripts(server, "client.py", "/tmp/client.py")
        server.close()

    print("Testing outside servers...")
    for server in outside_servers:
        server = connect_to_server(server)
        deploy_scripts(server, "server.py", "/tmp/server.py")
        deploy_scripts(server, "client.py", "/tmp/client.py")
        server.close()

    dst_port = 1030
    num_experiments = len(inside_servers) * len(outside_servers) * len(payloads) * 2
    exp_num = 1
    print(f"Running {num_experiments} experiments...")
    for inside_server in inside_servers:
        for outside_server in outside_servers:
            for payload in payloads:
                print(f"Running experiment {payload}: {inside_server['host']} -> {outside_server['host']}, {exp_num}/{num_experiments}")
                res = run_experiment(inside_server, outside_server, payload, packet_count, wait, dst_port, server_timeout)
                results_file.write(res + "\n")
                exp_num += 1
                dst_port += 1
                print(f"Running experiment {payload}: {outside_server['host']} -> {inside_server['host']}, {exp_num}/{num_experiments}")
                res = run_experiment(outside_server, inside_server, payload, packet_count, wait, dst_port, server_timeout)
                results_file.write(res + "\n")
                exp_num += 1
                dst_port += 1
    results_file.close()