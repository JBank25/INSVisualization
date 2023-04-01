import socket
import asyncio
import time
import json
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 10002)
sock.connect(server_address)

imu_data_queue = asyncio.Queue(-1)

imu_dummy_data = [30.288958, -97.735399]

def send_imu():

    while True:
        data = json.dumps(imu_dummy_data)
        sock.sendall(data.encode())
        time.sleep(1)
        response = sock.recv(1024)
        #if response == b'1':
            #print("Recieved '1' from socket")
        #else:
            #("recieved unexpected response")
        imu_dummy_data[0] += .00005
        imu_dummy_data[1] += .00005

send_imu()