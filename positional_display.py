import sys, pygame
from pygame.locals import *
import socket
import json
import threading
import queue

HOST = 'localhost'
PORT = 10002
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
                try:
                    data = conn.recv(128)
                    print(type(data))
                    if not data:
                        break
                    json_received = data.decode('utf-8')
                    json_list = json.loads(json_received)
                    print("Received: ", json_list)
                    imu_data_queue.put(json_list)
                    conn.sendall(b'1')
                except socket.error:
                    conn, addr = sock.accept()



#start a separate thread to handle incoming data
recv_thread = threading.Thread(target=receive_data)
recv_thread.start()



pygame.init()

size = width, height = 1000, 700
grey = 200, 200, 200
w, h = 5, 10

speed = [0, 0, 0]
pos = [width/2-w, height/2-h]

cen_x, cen_y = pos[0], pos[1]
r = Rect(pos[0], pos[1], w, h)

screen = pygame.display.set_mode(size)
screen_rect = screen.get_rect()
font = pygame.font.SysFont(None, 24)
t = 30

def set_speed(x, y, z):
    speed[0] = x
    speed[1] = y
    speed[2] = z
    spd = font.render("Speed: x:%.3f, y:%.3f, z:%.3f" % (speed[0],speed[1],speed[2]), True, (0,0,0))
    return spd


def update_pos(data):
    pos[0] = data[0]
    pos[1] = data[1]
    latitude = font.render("Latitude: x:%.5f" % (pos[0]), True, (0, 0, 0))
    longitude = font.render("Longitude: x:%.5f" % (pos[1]), True, (0, 0, 0))
    return latitude, longitude


clock = pygame.time.Clock()

while True:
    clock.tick(t)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()

    if imu_data_queue.qsize() > 0:
        while imu_data_queue.qsize() > 0:
            pos = imu_data_queue.get()
            flag = 180
    else:
        pos = pos
    lat, lon = update_pos(pos)
    #spd = set_speed(0, 0, 0)

    r.clamp_ip(screen_rect)
    screen.fill(grey)
    pygame.draw.rect(screen, (0, 0, 0), r)

    #screen.blit(spd, (20, 20))
    screen.blit(lat, (20, 20))
    screen.blit(lon, (20, 50))

    r.update(pos[0], pos[1], w, h)


    pygame.display.flip()
