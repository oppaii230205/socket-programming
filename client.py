import os
import threading
from socket import socket, AF_INET, SOCK_STREAM

SERVER_HOST = 'localhost'
SERVER_PORT = 5000
NUM_CHUNKS = 4  # Số lượng chunk cố định

def download_chunk(file_name, chunk_index):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    
    file_size, chunk_size = map(int, client_socket.recv(1024).decode('utf-8').split(','))

    client_socket.sendall(str(chunk_index).encode('utf-8'))
    
    chunk_data = b''
    expected_size = chunk_size if chunk_index < NUM_CHUNKS - 1 else file_size - chunk_index * chunk_size;
    while len(chunk_data) < expected_size:
        data = client_socket.recv(expected_size - len(chunk_data))
        if not data:
            break
        chunk_data += data
    
    with open(file_name, 'w+b') as file:
        file.seek(chunk_index * chunk_size)
        file.write(chunk_data)
    
    client_socket.close()

def start_client(file_name):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    
    file_size, chunk_size = map(int, client_socket.recv(1024).decode('utf-8').split(','))
    client_socket.close()
    
    #with open(file_name, 'wb') as file:
    #    file.truncate(file_size)
    
    threads = []
    for chunk_index in range(NUM_CHUNKS):
        thread = threading.Thread(target=download_chunk, args=(file_name, chunk_index))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()
    
    print(f"File {file_name} downloaded successfully.")

if __name__ == "__main__":
    file_name = 'client_1.txt'
    start_client(file_name)
