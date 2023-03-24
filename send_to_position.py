import socket
import asyncio
import time
import json
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = ('localhost', 10002)
sock.connect(server_address)

imu_data_queue = asyncio.Queue(-1)

imu_dummy_data = [10,5]

def send_imu():

    while True:
        data = json.dumps(imu_dummy_data)
        sock.sendall(data.encode())
        time.sleep(1)
        response = sock.recv(1024)
        if response == b'1':
            print("Recieved '1' from socket")
        else:
            print("recieved unexpected response")
        imu_dummy_data[0] += 20
        imu_dummy_data[1] += 10

send_imu()
