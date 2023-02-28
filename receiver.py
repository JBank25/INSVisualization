import socket
import json
import threading
import queue

# define the host and port to receive data on
HOST = 'localhost'
PORT = 10003
imu_data_queue = queue.Queue()
# create a socket and start listening for incoming connections
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen()

def receive_data():
    while True:
        # wait for a client to connect
        conn, addr = sock.accept()
        with conn:
            while True:
                data = conn.recv(52)
                if not data:
                    break
                json_received = data.decode('utf-8')
                json_list = json.loads(json_received)
                print("Received: ", json_list)
                imu_data_queue.put(json_list)
                conn.sendall(b'1')


# start a separate thread to handle incoming data
recv_thread = threading.Thread(target=receive_data)
recv_thread.start()

while(True):
    #kill program once qeueue has 100 entrie
    if imu_data_queue.qsize() > 100:
        break
    #write all the data to a file
    with open("socket_imu_test_data.txt", "a") as f:
        f.write(f"imu: {imu_data_queue.get()}\n")