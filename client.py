import os
import struct
import threading
from socket import socket, AF_INET, SOCK_STREAM

SERVER_HOST = 'localhost'
SERVER_PORT = 5000
NUM_CHUNKS = 4  # Fixed number of chunks

# Use a threading lock to ensure safe file writing
# file_write_lock = threading.Lock()

def send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, msglen)

def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

def download_chunk(file_name, chunk_index):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    
    # Send the file's name as well as index (offset) to server in format: filename.zip-offset
    send_msg(client_socket, (f"{file_name}-{chunk_index}".encode('utf-8')))

    msg = recv_msg(client_socket)
    file_size, chunk_size = map(int, msg.decode('utf-8').split(','))
    print(f"=====> file_size: {file_size}, chunk_size: {chunk_size}, chunk_download_index {chunk_index}")
    
    # chunk_data = b''
    # expected_size = chunk_size if chunk_index < NUM_CHUNKS - 1 else file_size - chunk_index * chunk_size;
    chunk_data = recv_msg(client_socket)
    
    # For testing purpose
    '''
    with file_write_lock:
        with open(file_name.split('.')[0] + '_client.txt', 'w+b') as file:
            file.seek(chunk_index * chunk_size)
            file.write(chunk_data)
    '''
    with open(file_name.split('.')[0] + '_client.txt', 'w+b') as file:
        file.seek(chunk_index * chunk_size)
        file.write(chunk_data)
        
    client_socket.close()

def start_client():
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    
    # Select file to be downloaded
    file_name = 'server_1.txt'

    # file_size, chunk_size = map(int, client_socket.recv(1024).decode('utf-8').split(','))
    # client_socket.sendall("none".encode('utf-8'))
    client_socket.close()
    
    # with open(file_name, 'wb') as file:
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
    #file_name = 'client_1.txt'
    start_client()
