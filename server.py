import os
import threading
from socket import socket, AF_INET, SOCK_STREAM

SERVER_HOST = 'localhost'
SERVER_PORT = 5000
NUM_CHUNKS = 4  # Số lượng chunk cố định

def handle_client(client_socket, file_path):
    file_size = os.path.getsize(file_path)
    chunk_size = file_size // NUM_CHUNKS
    client_socket.sendall(f"{file_size},{chunk_size}".encode('utf-8'))
    # print(f"{file_size},{chunk_size}");

    with open(file_path, 'rb') as file:
        while True:
            chunk_request = client_socket.recv(1024).decode('utf-8')
            if not chunk_request:
                break
            chunk_index = int(chunk_request)
            file.seek(chunk_index * chunk_size)

            if chunk_index < NUM_CHUNKS - 1:
                chunk_data = file.read(chunk_size)
            else:
                chunk_data = file.read(file_size - chunk_index * chunk_size)

            print(f"Sending data from byte: {chunk_index * chunk_size}")
            client_socket.sendall(chunk_data)
    client_socket.close()

def start_server(file_path):
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        # print(f"Client {client_address} connected")
        client_handler = threading.Thread(target=handle_client, args=(client_socket, file_path))
        client_handler.start()

if __name__ == "__main__":
    file_path = 'server_1.txt'
    start_server(file_path)
