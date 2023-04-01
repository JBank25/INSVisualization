import sys, pygame
from pygame.locals import *
import socket
import json
import threading
import queue

import math
import requests
from io import BytesIO
from PIL import Image

def deg2num(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
  return (xtile, ytile)

def num2deg(xtile, ytile, zoom):
  """
  http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
  This returns the NW-corner of the square.
  Use the function with xtile+1 and/or ytile+1 to get the other corners.
  With xtile+0.5 & ytile+0.5 it will return the center of the tile.
  """
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)

def getImageCluster(lat_deg, lon_deg, delta_lat,  delta_long, zoom):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}
    smurl = r"http://a.tile.openstreetmap.org/{0}/{1}/{2}.png"
    xmin, ymax = deg2num(lat_deg, lon_deg, zoom)
    xmax, ymin = deg2num(lat_deg + delta_lat, lon_deg + delta_long, zoom)

    bbox_ul = num2deg(xmin, ymin, zoom)
    bbox_ll = num2deg(xmin, ymax + 1, zoom)

    bbox_ur = num2deg(xmax + 1, ymin, zoom)
    bbox_lr = num2deg(xmax + 1, ymax +1, zoom)

    Cluster = Image.new('RGB',((xmax-xmin+1)*256-1,(ymax-ymin+1)*256-1) )
    for xtile in range(xmin, xmax+1):
        for ytile in range(ymin,  ymax+1):
            try:
                imgurl=smurl.format(zoom, xtile, ytile)
                imgstr = requests.get(imgurl, headers=headers)
                tile = Image.open(BytesIO(imgstr.content))
                Cluster.paste(tile, box=((xtile-xmin)*255 ,  (ytile-ymin)*255))
            except:
                print("Couldn't download image")
                tile = None

    return Cluster, [bbox_ll[1], bbox_ll[0], bbox_ur[1], bbox_ur[0]]


def getMapping(lat, lon):
    lat_deg, lon_deg, delta_lat,  delta_long, zoom = lat-0.0025/2, lon-0.0025/2, 0.0025,  0.0025, 17
    a, bbox = getImageCluster(lat_deg, lon_deg, delta_lat, delta_long, zoom)
    # list of points to display (long, lat)
    x = (lat-bbox[1])/(bbox[3]-bbox[1])
    y = (lon-bbox[0])/(bbox[2]-bbox[0])
    return a, bbox[0], bbox[2], bbox[1], bbox[3]


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
                    #print(type(data))
                    if not data:
                        break
                    json_received = data.decode('utf-8')
                    json_list = json.loads(json_received)
                    imu_data_queue.put(json_list)
                    conn.sendall(b'1')
                except socket.error:
                    conn, addr = sock.accept()

def update_pos(data):
    pos[0] = data[0]
    pos[1] = data[1]
    latitude = font.render("Latitude: x:%.8f" % (pos[0]), True, (0, 0, 0))
    longitude = font.render("Longitude: x:%.8f" % (pos[1]), True, (0, 0, 0))
    return latitude, longitude

def getCoord(llon, ulon, llat, ulat, lat, lon, w, h):
    x = (lat - llat) / (ulat - llat)
    y = (lon - llon) / (ulon - llon)
    return x*w, (1-y)*h


#start a separate thread to handle incoming data
recv_thread = threading.Thread(target=receive_data)
recv_thread.start()

pos = [30.288958, -97.735399]

a, llon, ulon, llat, ulat = getMapping(pos[0], pos[1])

a.save('background.png')
pygame.init()
size = width, height = a.width, a.height

grey = 200, 200, 200
w, h = 5, 5
r = Rect(pos[0], pos[1], w, h)

screen = pygame.display.set_mode(size)
screen_rect = screen.get_rect()
font = pygame.font.SysFont(None, 24)
bg = pygame.image.load('background.png').convert()

t = 1
count = 0

clock = pygame.time.Clock()

#INSIDE OF THE GAME LOOP
while True:
    clock.tick(t)

    screen.fill((255,255,255))

    lat, lon = update_pos(pos)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()

    if imu_data_queue.qsize() > 0:
        while imu_data_queue.qsize() > 0:
            pos = imu_data_queue.get()
            flag = 180
    else:
        pos = pos

    if count == 5:
        count = 0
        t_a, t_llon, t_ulon, t_llat, t_ulat = getMapping(pos[0], pos[1])
        if (t_a.width and t_a.height) == 511:
            t_a.save('background.png')
            bg = pygame.image.load('background.png').convert()
            llon, ulon, llat, ulat = t_llon, t_ulon, t_llat, t_ulat
    else:
        count += 1


    x, y = getCoord(llon, ulon, llat, ulat, pos[0], pos[1], a.width, a.height)

    screen.blit(bg,(0,0))
    r.clamp_ip(screen_rect)
    pygame.draw.rect(screen, (0, 0, 255), r)
    screen.blit(lat, (20, 20))
    screen.blit(lon, (20, 50))
    r.update(x, y, w, h)
    pygame.display.flip()