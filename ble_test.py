import asyncio
from bleak import BleakClient
from bleak import discover
from bleak import BleakScanner
import sys
import struct
import socket
import json

BLE_UUID_IMU_VALUE = "beb5483e-36e1-4688-b7f5-ea07361b26a8"  # "C8F88594-2217-0CA6-8F06-A4270B675D69"
BLE_UUID_GPS_VALUE = "beb5483e-36e1-4688-b7f5-ea07361b26a9"  # "C8F88594-2217-0CA6-8F05-A4270B675D69"
num_notifications = 0  # number of notifications received, debug purposes
imu_data_queue = asyncio.Queue(-1)  # queue for storing imu data

# create a TCP/IP socket
sock_gps = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_orientation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

address_gps = ('localhost', 10002)
address_orientation = ('localhost', 10003)

sock_gps.connect(address_gps)
sock_orientation.connect(address_orientation)


async def process_imu_data():
    """
    This coroutine processes the IMU data from the queue.
    Probably where we should be doing some visulization. stuff
    """
    while True:
        imu_data = await imu_data_queue.get()
        # only send the last 3 entries in the list
        imu_data = json.dumps(imu_data[-3:])

        print(f"Sending IMU data: {imu_data}")
        sock_orientation.sendall(imu_data.encode())
        # loop until we receive a '1' back from the socket
        while True:
            response = sock_orientation.recv(1024)
            if response == b'1':
                print("Received '1' from socket")
                break
            else:
                print(f"Received unexpected response from socket: {response}")


async def check_imu_data_queue():
    """
    This coroutine checks the IMU data queue for new data.
    """
    while True:
        if not imu_data_queue.empty():
            print(f"New IMU data available: {imu_data_queue.qsize()} items in queue.")
        await asyncio.sleep(1)  # sleep for 100ms before checking again


async def imu_handler(sender, data):
    """
    This function is called when a notification is received from the IMU.
    It will unpack the data and put it into the queue, rounding to 3 decimal places.
    """
    print(data)
    imu_data = struct.unpack("<Bfff", data)  # reading data from BLE, 13 floats
    # imu_data = [round(x, 3) for x in imu_data]          #rounding to 3 decimal places
    print(f"Received IMU data: {imu_data}")
    # writing data to file
    with open("imu_data.txt", "a") as f:
        f.write(f"imu: {', '.join(str(x) for x in imu_data)}\n")
    await imu_data_queue.put(imu_data)                  #putting data into queue


async def gps_handler(sender, data):
    global num_notifications
    num_notifications += 1
    gps_packet = struct.unpack("<Bff", data)
    print(f"*************Received GPS data: {gps_packet}**********************")
    # only send the last 3 entries in the list
    gps_data = json.dumps(gps_packet[-2:])
    sock_gps.sendall(gps_data.encode())
    # loop until we receive a '1' back from the socket
    while True:
        response = sock_gps.recv(1024)
        if response == b'1':
            print("Received '1' from socket")
            break
        else:
            print(f"Received unexpected response from socket: {response}")


async def main():
    """
    This is the main function that will be called when the program is run.
    Scans for the Arduino Nano 33 BLE and then connects to it.
    Once connection is established, it will start listening for notifications.
    Currently it will listen for notifications from the IMU and GPS.
    """
    devices = await BleakScanner.discover()
    for d in devices:  # find the Arduino Nano 33 BLE
        print(d)
        if d.name == "ESP32":
            async with BleakClient(d.address) as client:  # connect to the device
                print("Connected to device: ")
                await client.start_notify(BLE_UUID_IMU_VALUE, imu_handler)  # start listening for notifications from IMU
                await client.start_notify(BLE_UUID_GPS_VALUE, gps_handler)  # start listening for notifications from GPS
                processing_task = asyncio.create_task(process_imu_data())   # start the coroutine to process the IMU data
                loop = asyncio.get_event_loop()
                try:
                    print("Press 'q' to exit")
                    await loop.run_in_executor(None, lambda: sys.stdin.read(1))
                except KeyboardInterrupt:
                    pass


asyncio.run(main())
