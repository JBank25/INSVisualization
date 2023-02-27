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

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import time
import multiprocessing as mp

pygame.init()
display = (800, 600)

arlen = 1.

screen = pygame.display.set_mode(display, DOUBLEBUF|OPENGL)

# Set up the OpenGL perspective
glMatrixMode(GL_PROJECTION)
gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
glMatrixMode(GL_MODELVIEW)
glTranslatef(0.0, 0.0, -5.0)

# Set up the initial camera position and orientation
camera_x, camera_y = 0, 0
camera_rot_x, camera_rot_y = 0, 0
mouse_down = False

# Define the vertices
vertices= (
    (-0.5, -0.27, -1.5),
    (-0.5, 0.28, -1.5),
    (-1.5, 0.28, -1.5),
    (-1.5, -0.27, -1.5),
    (-0.5, -0.27, -0.5),
    (-0.5, 0.28, -0.5),
    (-1.5, -0.27, -0.5),
    (-1.5, 0.28, -0.5),
    (1.5, -0.27, -1.5),
    (1.5, 0.28, -1.5),
    (0.5, 0.28, -1.5),
    (0.5, -0.27, -1.5),
    (1.5, -0.27, -0.5),
    (1.5, 0.28, -0.5),
    (0.5, -0.27, -0.5),
    (0.5, 0.28, -0.5),
    (1.5, -0.27, 0.5),
    (1.5, 0.28, 0.5),
    (0.5, 0.28, 0.5),
    (0.5, -0.27, 0.5),
    (1.5, -0.27, 1.5),
    (1.5, 0.28, 1.5),
    (0.5, -0.27, 1.5),
    (0.5, 0.28, 1.5),
    (-0.5, -0.27, 0.5),
    (-0.5, 0.28, 0.5),
    (-1.5, 0.28, 0.5),
    (-1.5, -0.27, 0.5),
    (-0.5, -0.27, 1.5),
    (-0.5, 0.28, 1.5),
    (-1.5, -0.27, 1.5),
    (-1.5, 0.28, 1.5)
    )

vertAX = (
    (333,0,0),
    (-333.5,0,0),
    (0,333.5,0),
    (0,-333.5,0),
    (0,0,333.5),
    (0,0,-333.5)
    )

vertArrow = (
    (0,0,0),
    (0,arlen,0),
    (.5,.8,0),
    (-.5,.8,0)
    )

# Define the edges that make up the object
edges = (
    (0,1),
    (0,3),
    (0,4),
    (2,1),
    (2,3),
    (2,7),
    (6,3),
    (6,4),
    (6,7),
    (5,1),
    (5,4),
    (5,7),
    (0+8,1+8),
    (0+8,3+8),
    (0+8,4+8),
    (2+8,1+8),
    (2+8,3+8),
    (2+8,7+8),
    (6+8,3+8),
    (6+8,4+8),
    (6+8,7+8),
    (5+8,1+8),
    (5+8,4+8),
    (5+8,7+8),
    (0+2*8,1+2*8),
    (0+2*8,3+2*8),
    (0+2*8,4+2*8),
    (2+2*8,1+2*8),
    (2+2*8,3+2*8),
    (2+2*8,7+2*8),
    (6+2*8,3+2*8),
    (6+2*8,4+2*8),
    (6+2*8,7+2*8),
    (5+2*8,1+2*8),
    (5+2*8,4+2*8),
    (5+2*8,7+2*8),
    (0+3*8,1+3*8),
    (0+3*8,3+3*8),
    (0+3*8,4+3*8),
    (2+3*8,1+3*8),
    (2+3*8,3+3*8),
    (2+3*8,7+3*8),
    (6+3*8,3+3*8),
    (6+3*8,4+3*8),
    (6+3*8,7+3*8),
    (5+3*8,1+3*8),
    (5+3*8,4+3*8),
    (5+3*8,7+3*8)
)

edgeAX = (
    (0,1),
    (2,3),
    (4,5)
    )

edgeArrow = (
    (0,1),
    (1,2),
    (1,3)
    )

# Set up the initial positions and rotations
starting_rot = [[20,103,-4],[20,103,-4],[20,103,-4],[20,103,-4]]
len_drone_rots = 10000
drone_pos = [0, 0, 0]
drone_rotation = starting_rot[0]# * len_drone_rots#[20,103,-4]
ax_pos = [0, 0, 0]
ax_rotation = starting_rot[1]
arrow_pos = [0,0,0]
arrow_rotation = starting_rot[2]

# Define a function to draw a drone given its rotation
def draw_drone(pos, rotation, cam):
    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glRotatef(rotation[0]+cam[0], 1, 0, 0)
    glRotatef(rotation[1]+cam[1], 0, 1, 0)
    glRotatef(rotation[2], 0, 0, 1)
    glBegin(GL_LINES)
    for edge in edges:
        for vertex in edge:
            glVertex3fv(vertices[vertex])
    glEnd()
    glPopMatrix()

def draw_axis(pos, rotation, cam):
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2.5)
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glRotatef(rotation[0]+cam[0], 1, 0, 0)
    glRotatef(rotation[1]+cam[1], 0, 1, 0)
    glRotatef(rotation[2], 0, 0, 1)
    glBegin(GL_LINES)
    for edge in edgeAX:
        for vertex in edge:
            glVertex3fv(vertAX[vertex])
    glEnd()
    glPopMatrix()

def draw_arrow(pos, rotation, cam):
    glColor3f(0.5, 0.5, 0.5)
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glRotatef(rotation[0]+cam[0], 1, 0, 0)
    glRotatef(rotation[1]+cam[1], 0, 1, 0)
    glRotatef(rotation[2], 0, 0, 1)
    glBegin(GL_LINES)
    for edge in edgeArrow:
        for vertex in edge:
            glVertex3fv(vertArrow[vertex])
    glEnd()
    glPopMatrix()
    

def display_drone_rotation(rotation):
    rotation_text = ['','','']
    #rotation_num = [0.,0.,0.]
    rotation_text[2] = "x:  {:.3f}°".format((rotation[0]-starting_rot[3][0])%360.)
    rotation_text[1] = "y:  {:.3f}°".format((rotation[1]-starting_rot[3][1])%360.)
    rotation_text[0] = "z:  {:.3f}°".format((rotation[2]-starting_rot[3][2])%360.)
    for i in range(3):
        drawText(10,(i+1)*30,rotation_text[i])

def drawText(x, y, text):                                                
    textSurface = font.render(text, True, (255, 255, 66, 255), (0, 66, 0, 255))
    textData = pygame.image.tostring(textSurface, "RGBA", True)
    glWindowPos2d(x, y)
    glDrawPixels(textSurface.get_width(), textSurface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, textData)

    

# Set up the game loop
x = list(np.random.uniform(-.5,.5,[1000,]))
y = list(np.random.uniform(-.5,.5,[1000,]))
z = list(np.random.uniform(-.5,.5,[1000,]))
rot = [0.]*1000
rot0 = [0.25]
idx = -1
font = pygame.font.Font(None, 30)
glEnable(GL_DEPTH_TEST)
cam = [0.,0.]


async def process_imu_data():
    """
    This coroutine processes the IMU data from the queue.
    Probably where we should be doing some visulization. stuff
    """
    while True:
        imu_data = await imu_data_queue.get()
        #print(f"Processing IMU data: {imu_data}")


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
    devices = await BleakScanner.discover()
    for d in devices:                       #find the Arduino Nano 33 BLE
        if d.name == "Arduino Nano 33 BLE": #name should be the name of your device
            print("Found device: " + d.name)
            async with BleakClient(d.address) as client:    #connect to the device
                await client.start_notify(BLE_UUID_IMU_VALUE, imu_handler)  #start listening for notifications from IMU
                await client.start_notify(BLE_UUID_GPS_VALUE, gps_handler)  #start listening for notifications from GPS
                processing_task = asyncio.create_task(process_imu_data())   # start the coroutine to process the IMU data
                loop = asyncio.get_event_loop()                     
                try:
                    print("Press 'q' to exit")
                    await loop.run_in_executor(None, lambda: sys.stdin.read(1))
                except KeyboardInterrupt:
                    pass
asyncio.run(main())

def getOrientation(imu, i):
    if not imu_data_queue.empty():
        return imu[i]
    else return 0

pygame.time.wait(5000)
while True:
    start = time.time()
    idx = (idx+1)%1000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_down = True
            mouse_start_pos = pygame.mouse.get_pos()
        elif event.type == pygame.MOUSEBUTTONUP:
            mouse_down = False
        elif event.type == pygame.MOUSEMOTION and mouse_down:
            mouse_pos = pygame.mouse.get_pos()
            camera_rot_y += (mouse_pos[0] - mouse_start_pos[0]) / 5.0
            cam[1] = camera_rot_y
            camera_rot_x += (mouse_pos[1] - mouse_start_pos[1]) / 5.0
            cam[0] = camera_rot_x
            mouse_start_pos = mouse_pos
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glClearColor(0.18431372549, 0.501960784314, 0.0352941176471, 0) # Set the background color to blue
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    glTranslatef(camera_x, camera_y, -5.0)
    drone_rotation[0] += get_orientation(imu_data, 10)#rotates like I would backflip
    drone_rotation[1] += get_orientation(imu_data, 11)#rotates like I would spin
    drone_rotation[2] += get_orientation(imu_data, 12)#rotates like I would cartwheel
    # Draw the objects
    draw_axis(ax_pos, ax_rotation, cam)
    draw_drone(drone_pos, drone_rotation, cam)
    display_drone_rotation(drone_rotation)
    # Update the display
    pygame.display.flip()

    # Set the framerate
    now = int(1000*(time.time()-start))
    if (now) < 20:
        #print(now)
        pygame.time.wait(20-(now))
    else:
        #print(now)
        print('Im slow')
    while True:
        idx += 1
