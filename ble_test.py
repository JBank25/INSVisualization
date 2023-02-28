import asyncio
from bleak import BleakClient
from bleak import discover
from bleak import BleakScanner
import sys
import struct
import multiprocessing as mp

BLE_UUID_IMU_VALUE = "C8F88594-2217-0CA6-8F06-A4270B675D69" 
BLE_UUID_GPS_VALUE = "C8F88594-2217-0CA6-8F05-A4270B675D69"
num_notifications = 0   #number of notifications received, debug purposes
imu_data_queue = asyncio.Queue(-1)    #queue for storing imu data

async def process_imu_data(display_queue):
    """
    This coroutine processes the IMU data from the queue.
    Probably where we should be doing some visulization. stuff
    """
    while True:
        imu_data = await imu_data_queue.get()
        display_queue.put(imu_data)
        print(f"Processing IMU data: {imu_data}")


async def check_imu_data_queue():
    """
    This coroutine checks the IMU data queue for new data.
    """
    while True:
        if not imu_data_queue.empty():
            print(f"New IMU data available: {imu_data_queue.qsize()} items in queue.")
        await asyncio.sleep(1)  # sleep for 100ms before checking again

def populate_data_map_imu(imu_data):
    """
    This function populates a dictionary with the IMU data
    and returns the dictionary.
    """
    # Define the keys for the dictionary
    keys = ["ordinalID", "imuData", "roll", "pitch", "yaw"]
    data_dict = {}
    data_dict[keys[0]] = imu_data[0]
    data_dict[keys[1]] = imu_data[1:10]
    data_dict[keys[2]] = imu_data[10]
    data_dict[keys[3]] = imu_data[11]
    data_dict[keys[4]] = imu_data[12]
    return data_dict

async def imu_handler(sender, data):
    """
    This function is called when a notification is received from the IMU.
    It will unpack the data and put it into the queue, rounding to 3 decimal places.
    """
    imu_data = struct.unpack("<fffffffffffff", data)    #reading data from BLE, 13 floats
    imu_data = [round(x, 3) for x in imu_data]          #rounding to 3 decimal places
    await imu_data_queue.put(imu_data)                  #putting data into queue
    
async def gps_handler(sender, data):
    global num_notifications
    num_notifications += 1
    gps_data = struct.unpack("<fffff", data)
    with open("sensor_data.txt", "a") as f:
        f.write(f"gps: {', '.join(str(x) for x in gps_data)}\n")


async def main():
    """
    This is the main function that will be called when the program is run.
    Scans for the Arduino Nano 33 BLE and then connects to it.
    Once connection is established, it will start listening for notifications.
    Currently it will listen for notifications from the IMU and GPS.
    """
    display_queue = multiprocesessing.Queue()
    devices = await BleakScanner.discover()
    for d in devices:                       #find the Arduino Nano 33 BLE
        if d.name == "Arduino Nano 33 BLE": #name should be the name of your device
            print("Found device: " + d.name)
            async with BleakClient(d.address) as client:    #connect to the device
                await client.start_notify(BLE_UUID_IMU_VALUE, imu_handler)  #start listening for notifications from IMU
                await client.start_notify(BLE_UUID_GPS_VALUE, gps_handler)  #start listening for notifications from GPS
                processing_task = asyncio.create_task(process_imu_data(display_queue))   # start the coroutine to process the IMU data
                loop = asyncio.get_event_loop()                     
                try:
                    print("Press 'q' to exit")
                    await loop.run_in_executor(None, lambda: sys.stdin.read(1))
                except KeyboardInterrupt:
                    pass
asyncio.run(main())
