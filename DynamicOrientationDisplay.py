import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import time
import math

import socket
import json
import threading
import queue

HOST = 'localhost'
PORT = 10003
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen()


imu_data_queue = queue.Queue()

def receive_data():
    while True:
        # wait for a client to connect
        conn, addr = sock.accept()
        with conn:
            while True:
                data = conn.recv(64)
                #print(type(data))
                if not data:
                    break
                json_received = data.decode('utf-8')
                json_list = json.loads(json_received)
                #print("Received: ", json_list)
                imu_data_queue.put(json_list)
                conn.sendall(b'1')


#start a separate thread to handle incoming data
recv_thread = threading.Thread(target=receive_data)
recv_thread.start()

# define the host and port to receive data on

# create a socket and start listening for incoming connections


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
offset = [0, 0, 0]
len_drone_rots = 10000
drone_pos = [0, 0, 0]
drone_rotation = [0, 0, 0]# * len_drone_rots#[20,103,-4]
drone_rotation_last = [0,0,0]
ax_pos = [0, 0, 0]
ax_rotation = [0, 0, 0]
arrow_pos = [0,0,0]
arrow_rotation = [0,0,0]

# Define a function to draw a drone given its absolute rotation
def draw_drone(pos, rotation, cam):
    glColor3f(0.0, 0.0, 0.0)
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glRotatef(cam[0], 1, 0, 0)
    glRotatef(cam[1], 0, 1, 0)
    glRotatef(rotation[0], 1, 0, 0)
    glRotatef(rotation[1], 0, 1, 0)
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
    glRotatef(cam[0], 1, 0, 0)
    glRotatef(cam[1], 0, 1, 0)
    glRotatef(rotation[0], 1, 0, 0)
    glRotatef(rotation[1], 0, 1, 0)
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
    glRotatef(cam[0], 1, 0, 0)
    glRotatef(cam[1], 0, 1, 0)
    glBegin(GL_LINES)
    for edge in edgeArrow:
        for vertex in edge:
            glVertex3fv(vertArrow[vertex])
    glEnd()
    glPopMatrix()
    

def display_drone_rotation(rotation):
    rotation_text = ['','','']
    #rotation_num = [0.,0.,0.]
    rotation_text[2] = "x:  {:.3f}°".format((rotation[0]-offset[0])%360.)
    rotation_text[1] = "y:  {:.3f}°".format((rotation[1]-offset[1]-180)%360.)
    rotation_text[0] = "z:  {:.3f}°".format((rotation[2]-offset[2])%360.)
    for i in range(3):
        drawText(10,(i+1)*30,rotation_text[i])

def drawText(x, y, text):                                                
    textSurface = font.render(text, True, (255, 255, 66, 255), (0, 66, 0, 255))
    textData = pygame.image.tostring(textSurface, "RGBA", True)
    glWindowPos2d(x, y)
    glDrawPixels(textSurface.get_width(), textSurface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, textData)

    

# Set up the game loop
rot = [0.]*1000
rot0 = [0.25]
idx = -1
font = pygame.font.Font(None, 30)
glEnable(GL_DEPTH_TEST)
cam = [0.,0.]
lag = 0
xyz = [0]*3
zeros = [0]*3
last = [0]*3
flag = 0

##generate test xyz rotation data
##x = ([0] * 500) + [(i/10) for i in list(range(1, 1801))] + ([0] * 1300)
##c = 0
##r = 0
##

while True:
    start = time.time()
##    input tester
##    r = np.random.randint(0,3)
##    while r > 0:
##        imu_data_queue.put([x[c%3600],0,0])
##        c += 1
##        r -= 1
##    if idx%100==0:
##        print('c='+str(c))
##        print('offset:', offset)
##        print('drone_rotation:', drone_rotation)
##        print('xyz:', xyz)
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
    xc = 0#math.sin(math.radians(camera_rot_y)) * math.cos(math.radians(camera_rot_x))
    yc = 0#math.sin(math.radians(camera_rot_x))
    zc = 0#math.cos(math.radians(camera_rot_y)) * math.cos(math.radians(camera_rot_x))
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glClearColor(0.18431372549, 0.501960784314, 0.0352941176471, 0) # Set the background color to blue
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(0.0, 0.0, 1.0, xc, yc, zc, 0.0, 1.0, 0.0)
    glTranslatef(camera_x, camera_y, -5.0)
    #glRotatef(camera_rot_x, 1.0, 0.0, 0.0)
    #glRotatef(camera_rot_y, 0.0, 1.0, 0.0)
    # Rotate the drone
    if imu_data_queue.qsize() > 0:
        while imu_data_queue.qsize() > 0:
            xyz = imu_data_queue.get()
            flag = 180
    else:
        xyz = xyz
    drone_rotation[0] = xyz[1]+offset[0] #rotates like I would backflip
    drone_rotation[1] = xyz[2]+offset[1] #rotates like I would spin
    drone_rotation[2] = xyz[0]+offset[2]#rotates like I would cartwheel
    last = xyz.copy()
    #rot[idx] = 0
    # Draw the objects
    draw_axis(ax_pos, ax_rotation, cam)
    draw_drone(drone_pos, drone_rotation, cam)
    if flag == 0:
        display_drone_rotation([offset[0],offset[1]-180,offset[2]])
    else:
        display_drone_rotation(drone_rotation)
    # Update the display
    pygame.display.flip()
    # Set the framerate
    now = int(1000*(time.time()-start))
    if now+lag <= 30:
        pygame.time.wait(30-now-lag)
        lag = 0
    else:
        lag += now+lag-30
        #print('too slow', lag)
    if lag > 100:
        lag = 0
