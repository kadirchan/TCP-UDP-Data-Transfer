import os
import socket
import pickle
import threading
import math
import random

LARGE_OBJ_PATH = '../objects/large-'
SMALL_OBJ_PATH = '../objects/small-'

CHUNKSIZE = 4096
PORT = 12345
WINDOW_SIZE = 128

client_address = ('172.17.0.3', 55063)
server_address=('172.17.0.2', 3131)


lock = threading.Lock()

# Create socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(server_address)
sock.settimeout(1)

# sock_ack = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock_ack.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)

base = 0
next_seq_num = 0
available = WINDOW_SIZE
packets = []
objects = {}
object_list_for_client = {}


# It gets object name and chunk index and returns chunk and checksum
def get_chunks_from_object(object_name, chunk_index):
    chunks, checksum, file_size = objects[object_name]
    return chunks[chunk_index], checksum[chunk_index]

# It gets file path and returns chunks and file size
def open_file_and_split_chunks(file_path):
    file = open(file_path, 'rb')
    file_size = os.path.getsize(file_path)
    chunks = []
    while True:
        chunk = file.read(CHUNKSIZE)
        if not chunk:
            break
        chunks.append(chunk)
    file.close()
    return chunks, file_size

# Preparing packet buffers
for i in range(0, 10):
    large_obj_path = LARGE_OBJ_PATH + str(i) + '.obj'
    small_obj_path = SMALL_OBJ_PATH + str(i) + '.obj'

    large_obj_name = 'large-' + str(i) + '.obj'
    small_obj_name = 'small-' + str(i) + '.obj'

    # preparing file chunks and their size information
    large_chunks, large_file_size = open_file_and_split_chunks(large_obj_path)
    small_chunks, small_file_size = open_file_and_split_chunks(small_obj_path)

    objects[large_obj_name] = (large_chunks, math.ceil(large_file_size / CHUNKSIZE))
    objects[small_obj_name] = (small_chunks, math.ceil(small_file_size / CHUNKSIZE))

    object_list_for_client[large_obj_name] = (large_file_size, math.ceil(large_file_size / CHUNKSIZE))
    object_list_for_client[small_obj_name] = (small_file_size, math.ceil(small_file_size / CHUNKSIZE))


# Buffering packets
chunk_index = 0
control = True
while control:
    control = False
    # Sequencing packets like lrg-0-0, sml-0-0, lrg-0-1, sml-0-1, lrg-0-2, sml-0-2, ... but more homogenous
    for file_name in object_list_for_client.keys():
        if chunk_index < object_list_for_client[file_name][1]:
            packets.append((file_name, chunk_index, object_list_for_client[file_name][1], objects[file_name][0][chunk_index]))
            control = True
    chunk_index += 1  

# acked packets bit array
acked = [False] * len(packets)

# timers array of loop threads
timers = [None] * len(packets)

# It gets packet and sequence number and sends packet to client
def send_packet(packet, seq_num):
    global timers, acked

    # If packet is not acked, send it, start timer to resend if ack is not received after timeout
    if not acked[seq_num]:
        data = pickle.dumps((seq_num, packet))
        start_timer(seq_num)
        sock.sendto(data, client_address)
    # But if it is acked and stucked and tries to send again, cancel timer do nothing
    else:
        timers[seq_num].cancel()

# It gets sequence number and resends packet
def resend_packet(seq_num):
    global lock, next_seq_num, acked
    if seq_num < next_seq_num and not acked[seq_num]:
        send_packet(packets[seq_num], seq_num)

# It gets sequence number and starts timer for that sequence number
def start_timer(seq_num):
    global timers
    # If sequence number is acked but tries to start timer again, cancel timer
    if acked[seq_num]:
        timers[seq_num].cancel()
    else:
        # Give random timeout between 0.6 and 0.8 to timers to avoid burst of packets and congestion
        timeout = random.uniform(0.6, 0.8)
        timer = threading.Timer(timeout, resend_packet, [seq_num])
        timers[seq_num] = timer
        timer.start()

# It sends packets until all packets are sent
# It uses base, next_seq_num and available variables to control window size
# available = WINDOW_SIZE - (timers that are not acked yet)
# This uses sliding window protocol
def send_packets():
    global base, next_seq_num, available
    while base < len(packets):
        with lock:
            while next_seq_num < base + WINDOW_SIZE and next_seq_num < len(packets) and available > 0:
                send_packet(packets[next_seq_num], next_seq_num)
                available -= 1
                next_seq_num += 1

# It listens for acks and updates acked array and base and available variables on another thread
def listen_for_ack():
    global base, available
    while True:
        try:
            data, _ = sock.recvfrom(1024)
            ack = pickle.loads(data)
            #If received ack is has a timer, cancel it
            if timers[ack] is not None:
                timers[ack].cancel()
            
            with lock:
                acked[ack] = True
                available += 1
                if ack >= base:
                    base = ack + 1
        except socket.timeout:
            pass


threading.Thread(target=listen_for_ack).start()

send_packets()
