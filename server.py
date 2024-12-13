import os
import struct
import threading
from socket import socket, AF_INET, SOCK_STREAM

SERVER_HOST = 'localhost'
SERVER_PORT = 5000
NUM_CHUNKS = 4  # Fixed number of chunks

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

def handle_client(client_socket, client_address):    
    # Get name of the file to be downloaded from the client
    msg = recv_msg(client_socket)
    
    # The download list is requested
    if msg.decode('utf-8') == 'START':
        with open('text.txt', 'rb') as file:
            data = file.read()
            send_msg(client_socket, data)

        # Wait for the client to close connection
        msg = recv_msg(client_socket)
        
        if not msg:
            client_socket.close()
        return

    # Decode the msg to get the path of the file
    file_path = msg.decode('utf-8')

    # Calculate file_size and chunk_size for sending to clients 
    file_size = os.path.getsize(file_path)
    chunk_size = file_size // NUM_CHUNKS
    send_msg(client_socket, f"{file_size},{chunk_size}".encode('utf-8'))
    # print(f"{file_size},{chunk_size}")

    with open(file_path, 'rb') as file:
        # Receive chunk_index 
        msg = recv_msg(client_socket)

        # Not the client to send data to (the client that START the connection, not the DOWNLOADING client)
        if not msg:
            client_socket.close()
            return
        
        # Decode the msg to chunk_index
        chunk_index = int(msg.decode('utf-8'))

        # Seek the file's cursor to correct position
        file.seek(chunk_index * chunk_size)

        # Determine how many bytes are going to be read and sent 
        if chunk_index < NUM_CHUNKS - 1:
            chunk_data = file.read(chunk_size)
        else:
            chunk_data = file.read(file_size - chunk_index * chunk_size)
        
        print(f"Sending data from byte: {chunk_index * chunk_size}")
        send_msg(client_socket, chunk_data)
    
    client_socket.close()

def start_server():
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen()
    print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        # print(f"Client {client_address} connected")

        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

if __name__ == "__main__":
    # file_path = 'server_1.txt'
    start_server()
