#!/bin/bash

# Define variables
HOST="43.143.0.0"    # Target IP address or hostname
PORT="53"        # Target port

PAYLOAD="de7a012000010000000000010a6874747033636865636b036e657400000100010000291000000000000000"
INTERVAL=10         # Interval between sends in seconds

# Convert hex string to bytes
hex_to_bytes() {
    echo "$PAYLOAD" | xxd -r -p
}

# Infinite loop to send payload every 10 seconds
while true; do
    # Convert hex to bytes and send the payload via UDP using netcat (nc)
    hex_to_bytes | nc -u -w1 $HOST $PORT
    
    # Display a message indicating the payload was sent
    echo "Payload sent to $HOST:$PORT via UDP."
    
    # Wait for 10 seconds before sending the next payload
    sleep $INTERVAL
done

