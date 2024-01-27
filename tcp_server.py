import socket
import os

LARGE_OBJ_PATH = '../objects/large-'
SMALL_OBJ_PATH = '../objects/small-'

def send_file(client_socket, file_path):
    # Send the file content
    with open(file_path, 'rb') as file:
        while True:
            bytes_read = file.read(4096)
            if not bytes_read:
                break
            client_socket.sendall(bytes_read)
    # Wait for client to acknowledge
    client_socket.recv(1024)

def run_tcp_server(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', port))
    server_socket.listen(1)
    print(f"Server is listening on port {port}")

    while True:
        client_socket, addr = server_socket.accept()
        # print(f"Connection from {addr} has been established.")

        # Get the file size
        small_file_size = os.path.getsize('../objects/small-0.obj')
        large_file_size = os.path.getsize('../objects/large-0.obj')

        # Send the file sizes to the client
        client_socket.sendall(str(small_file_size).encode())

        # Wait for client to acknowledge
        client_socket.recv(1024)

        client_socket.sendall(str(large_file_size).encode())

        # Wait for client to acknowledge
        client_socket.recv(1024)

        # Send large file first
        for i in range(0, 10):
            send_file(client_socket, LARGE_OBJ_PATH + str(i) + '.obj')
            send_file(client_socket, SMALL_OBJ_PATH + str(i) + '.obj')

        print("All files have been sent.")
        client_socket.close()
        break

    server_socket.close()

run_tcp_server(12345)
        

