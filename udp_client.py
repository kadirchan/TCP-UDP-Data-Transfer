import socket
import time
import pickle
import hashlib
import threading
import concurrent.futures

IP='172.17.0.2'
PORT=12345
ACK_ADRESS=('172.17.0.2', 3131)
LISTEN_IP='172.17.0.3'
LISTEN_PORT=55063
CHUNKSIZE=4096


lock = threading.Lock()

# we measure total packet size as 2480 in given objects and use this value
packets = [None]*2480
received=[False]*2480

start_time = time.time()
not_started = True

received_packets = set()

# Create socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
sock.bind((LISTEN_IP, LISTEN_PORT))
sock.settimeout(1.5)

# This time client listens and server sends packets
print("Listening on: ", LISTEN_IP, LISTEN_PORT)

def listen_for_packets():
    global not_started
    # Count is used to check if we received all packets
    count = 0
    while count < 2480:
        try:
            # Receive packet
            data, addr = sock.recvfrom(4200)

            # Start timer for measuring elapsed time
            if not_started:
                start_time = time.time()
                not_started = False
            # Parse packet
            seq_num, packet = pickle.loads(data)

            # Send ack
            ack_data = pickle.dumps(seq_num)
            sock.sendto(ack_data, ACK_ADRESS)

            # If we didn't receive this packet before, add it to packets
            if not received[seq_num] :
                received[seq_num] = True
                packets[seq_num] = (packet[0], packet[3])
                count += 1
        except socket.timeout:
            pass
            
    # Write packets to files after receiving all packets
    for packet in packets:
        with open('../objects/' + packet[0], 'ab') as f:
            f.write(packet[1])

    print("Received all packets, elapsed time: ", time.time() - start_time)
    sock.close()
        
listen_for_packets()
