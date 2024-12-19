import os
import random
import struct
import threading
import signal # For catching Ctrl C
import time
from socket import socket, AF_INET, SOCK_STREAM

from tqdm import tqdm

SERVER_HOST = '192.168.247.129'
SERVER_PORT = 5000
NUM_CHUNKS = 4  # Fixed number of chunks

class DownloadProcess:
    def __init__(self, file_name, chunk_index):
        self.file_name = file_name
        self.chunk_index = chunk_index

download_list = []
current_list_size = 0

# Use a threading lock to ensure safe file writing
# file_write_lock = threading.Lock()

def signal_handler(sig, frame):
    print('You\'ve pressed Ctrl+C! The program will be terminated now...')
    exit(1)

def send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def recv_msg(sock, download_process=None):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, msglen, download_process)

def recvall(sock, n, download_process=None):
    # Helper function to recv n bytes or return None if EOF is hit
    if not download_process:
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data
    else:
        data = bytearray()
        with tqdm(total=n, ncols=100, unit='B', unit_scale=True, desc=f"Downloading {download_process.file_name} part {download_process.chunk_index + 1}", position=download_process.chunk_index, leave=False) as pbar:
            prev_len = 0
            while len(data) < n:
                packet = sock.recv(n - len(data))
                if not packet:
                    return None
                data.extend(packet)
                pbar.update(len(data)- prev_len)
                time.sleep(.30 * random.random())
                prev_len = len(data)
        return data

def update_download_list():
    global download_list

    starttime = time.monotonic()
    
    while True:
        download_list.clear()
        with open('input.txt', 'r') as file:
            #download_list = list(map(str.strip, file.readlines()))
            download_list = list(map(str.strip, file))
        
        # print("tick")
        time.sleep(5.0 - ((time.monotonic() - starttime) % 5.0))

def get_list():
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    
    # Send the file's name to server
    send_msg(client_socket, ('START'.encode('utf-8')))

    # Receive the data of the download list
    data = recv_msg(client_socket)

    # Write data to the file
    with open('text_from_server.txt', 'wb') as file:
        file.write(data)
    
    #Print the list to the console
    print('>> ----------  DOWNLOAD LIST  ---------- <<')
    with open('text_from_server.txt', 'r') as file:
        print(file.read())

    print('>> ----------  END OF LIST  ---------- <<')
    
    print("\nEnter the file to be downloaded in 'input.txt'...")

    # Close connection
    client_socket.close()

def download_chunk(file_name, chunk_index):
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    
    # Send the file's name to server
    send_msg(client_socket, (file_name.encode('utf-8')))

    # Receive msg that contains file_size and chunk_size
    msg = recv_msg(client_socket)

    file_size, chunk_size = map(int, msg.decode('utf-8').split(','))
        
    # Send the chunk_index (offset) to server to download the specific chunk
    send_msg(client_socket, f"{chunk_index}".encode('utf-8'))
    
    # Reveive the chunk from server
    download_process = DownloadProcess(file_name, chunk_index)
    chunk_data = recv_msg(client_socket, download_process)
    
    # Write data to the client's file
    '''
    with file_write_lock:
        with open(file_name.split('.')[0] + '_client.' + file_name.split('.')[1], 'r+b') as file:
            file.seek(chunk_index * chunk_size)
            file.write(chunk_data)
    '''

    
    with open(file_name, 'r+b') as file:
        file.seek(chunk_index * chunk_size)
        file.write(chunk_data)
    
    
    client_socket.close()

def start_client():
    global download_list, current_list_size
    
    update_list_thread = threading.Thread(target=update_download_list, daemon=True) # daemon = True for terminate this thread when our main function ends
    update_list_thread.start()

    while True:
        # Select file to be downloaded
        if current_list_size >= len(download_list): # Not anything new
            continue
        
        file_name = download_list[current_list_size]
        
        # Establish a connection to the server
        client_socket = socket(AF_INET, SOCK_STREAM)
        client_socket.connect((SERVER_HOST, SERVER_PORT))

        # Send the file's name to server in format: filename.zip
        send_msg(client_socket, (file_name.encode('utf-8')))

        # Receive msg that contains file_size and chunk_size
        msg = recv_msg(client_socket)
        file_size, chunk_size = map(int, msg.decode('utf-8').split(','))
        
        client_socket.close() # Still needed because this socket is not for downloading

        # Truncate the file to the size that can the later 4 threads can write the data into
        with open(file_name, 'wb') as file:
            file.truncate(file_size)
        
        # Establish 4 connections to the server for downloading 4 chunks respectively
        threads = []
        for chunk_index in range(NUM_CHUNKS):
            thread = threading.Thread(target=download_chunk, args=(file_name, chunk_index))
            thread.start()
            threads.append(thread)
        
        # Wait for all the threads have finished
        for thread in threads:
            thread.join()
        
        tqdm.write(f"\nFile {file_name} downloaded successfully.")
        current_list_size += 1 # Update the number of downloaded file

if __name__ == "__main__":
    # Close the connection by pressing 'Ctrl + C'
    signal.signal(signal.SIGINT, signal_handler)
    
    get_list()
    start_client()