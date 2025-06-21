#!/bin/bash

# ----------------------------
# Configuration
# ----------------------------


# # Define the array of source ports
# src_ports=(
#     1 1000 2000 3000 4000 5000 6000 7000 8000 9000
#     10000 11000 12000 13000 14000 15000 16000 17000 18000 19000
#     20000 21000 22000 23000 24000 25000 26000 27000 28000 29000
#     30000 31000 32000 33000 34000 35000 36000 37000 38000 39000
#     40000 41000 42000 43000 44000 45000 46000 47000 48000 49000
#     50000 51000 52000 53000 54000 55000 56000 57000 58000 59000
#     60000 61000 62000 63000 64000 65000
# )

# # Define the base destination ports
# base_dst_ports=(
#     1 1000 2000 3000 4000 5000 6000 7000 8000 9000
#     10000 11000 12000 13000 14000 15000 16000 17000 18000 19000
#     20000 21000 22000 23000 24000 25000 26000 27000 28000 29000
#     30000 31000 32000 33000 34000 35000 36000 37000 38000 39000
#     40000 41000 42000 43000 44000 45000 46000 47000 48000 49000
#     50000 51000 52000 53000 54000 55000 56000 57000 58000 59000
#     60000 61000 62000 63000 64000 65000
# )

# Define the array of source ports
src_ports=(
    401 402 403 404 405 406 407 408 409 410 
    411 412 413 414 415 416 417 418 419 420 
    421 422 423 424 425 426 427 428 429 430 
    431 432 433 434 435 436 437 438 439 440
    441 442 443 444 445 446 447 448 449 450
)

# Define the base destination ports
base_dst_ports=(
    401 402 403 404 405 406 407 408 409 410
    411 412 413 414 415 416 417 418 419 420
    421 422 423 424 425 426 427 428 429 430
    431 432 433 434 435 436 437 438 439 440 
    441 442 443 444 445 446 447 448 449 450
)

# Destination IP addresses as an array
dst_ips=(
    "171.67.0.0"
    "171.67.0.0"
    "171.67.0.0"
    "171.67.0.0"
    "171.67.0.0"
    "171.67.0.0"
    "171.67.0.0"
    "171.67.0.0"
    "171.67.0.0"
    "171.67.0.0"
)

# Socket pool size (fixed)
socket_pool_size=1

# Number of iterations (should match the number of source ports)
num_iterations=${#src_ports[@]}

# Log file (optional)
log_file="async_quiche_client_execution.log"

# ----------------------------
# Main Loop for Each Destination IP
# ----------------------------
for dst_ip in "${dst_ips[@]}"; do
    # Spawn a new task for each destination IP in the background
    {
        echo "Starting execution for Destination IP: $dst_ip"

        # Shuffle src_ports array for each destination IP
        shuffled_src_ports=($(printf "%s\n" "${src_ports[@]}" | shuf))

        for ((i=0; i<num_iterations; i++)); do
            src_port=${shuffled_src_ports[i]}

            # Get the new destination ports (same as base destination ports in this case)
            new_dst_ports=("${base_dst_ports[@]}")

            # Convert destination ports array to comma-separated string
            dst_ports_str=$(IFS=, ; echo "${new_dst_ports[*]}")

            # Dynamically calculate the number of workers as half the number of destination ports
            num_dst_ports=${#new_dst_ports[@]}
            worker=$((num_dst_ports / 2))

            echo "----------------------------------------"
            echo "Iteration $((i+1)) for Destination IP $dst_ip:"
            echo "  Source Port: $src_port"
            echo "  Destination Ports: $dst_ports_str"
            echo "  Number of Workers: $worker"

            # Run the command, using the number of 'yes' lines equal to the number of destination ports
            yes 'google.com' | head -n $num_dst_ports | /root/quic-sni-sender/target/release/async_quiche_client \
                --dip "$dst_ip" \
                -p "$dst_ports_str" \
                --worker "$worker" \
                --sport "$src_port" \
                --socket-pool-size "$socket_pool_size" \
                --no-use-greater-srcports \
                --log "log_${src_port}_$dst_ip"

            # Delay for residual censorship
            sleep 181
        done

        echo "Execution for Destination IP $dst_ip completed."

    } &  # Run in the background
done

# Wait for all background tasks to complete
wait

echo "All iterations for all destination IPs have been executed."

