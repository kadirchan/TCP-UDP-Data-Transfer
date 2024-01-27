import socket
import time

LARGE_OBJ_PATH = '../objects/large-'
SMALL_OBJ_PATH = '../objects/small-'

IP = '172.17.0.2'
PORT = 12345

def receive_file(client_socket, file_save_path, file_size):
    # Receive the file content
    with open(file_save_path, 'wb') as file:
        bytes_received = 0
        while bytes_received < file_size:
            bytes_read = client_socket.recv(4096)
            if not bytes_read:
                break
            file.write(bytes_read)
            bytes_received += len(bytes_read)
    # print(f"Received {file_save_path}")
    client_socket.sendall("ACK".encode())


def run_tcp_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    # print(f"Connected to {IP} on port {PORT}")

    # Receive the file sizes
    small_file_size = int(client_socket.recv(1024).decode())

    # Acknowledge file size reception
    client_socket.sendall("ACK".encode())

    large_file_size = int(client_socket.recv(1024).decode())

    # Acknowledge file size reception
    client_socket.sendall("ACK".encode())


    # Receive large file first then small file
    start_time = time.time()
    for i in range(0, 10):
        large_file_save_path = LARGE_OBJ_PATH + str(i) + '.obj'
        small_file_save_path = SMALL_OBJ_PATH + str(i) + '.obj'

        receive_file(client_socket, large_file_save_path, large_file_size)
        receive_file(client_socket, small_file_save_path, small_file_size)

    end_time = time.time()
    print("All files have been received.")
    print(f"Time elapsed: {end_time - start_time} seconds")
    client_socket.close()

run_tcp_client()
