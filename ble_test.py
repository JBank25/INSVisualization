import asyncio
from bleak import BleakClient
from bleak import discover
from bleak import BleakScanner
import sys
import struct

BLE_UUID_IMU_VALUE = "C8F88594-2217-0CA6-8F06-A4270B675D69"
BLE_UUID_GPS_VALUE = "C8F88594-2217-0CA6-8F05-A4270B675D69"
num_notifications = 0

async def imu_handler(sender, data):
    #read in the data, unpack and only store floats to 3 decimals precision
    imu_data = struct.unpack("<ffffffffff", data)
    imu_data = struct.unpack("<ffffffffff", data)
    with open("sensor_data.txt", "a") as f:
        f.write(f"imu: {', '.join(str(x) for x in imu_data)}\n")
async def gps_handler(sender, data):
    global num_notifications
    num_notifications += 1
    gps_data = struct.unpack("<fffff", data)
    with open("sensor_data.txt", "a") as f:
        f.write(f"gps: {', '.join(str(x) for x in gps_data)}\n")
async def main():
    devices = await BleakScanner.discover()
    for d in devices:
        if d.name == "Arduino Nano 33 BLE":
            print("Found device: " + d.name)
            async with BleakClient(d.address) as client:
                await client.start_notify(BLE_UUID_IMU_VALUE, imu_handler)
                await client.start_notify(BLE_UUID_GPS_VALUE, gps_handler)
                loop = asyncio.get_event_loop()
                try:
                    print("Press 'q' to exit")
                    await loop.run_in_executor(None, lambda: sys.stdin.read(1))
                except KeyboardInterrupt:
                    pass
asyncio.run(main())
