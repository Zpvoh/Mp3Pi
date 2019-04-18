# -*- coding:utf-8 -*-

from luma.core.interface.serial import i2c, spi
from luma.core.render import canvas
from luma.core import lib

import os
from multiprocessing import Process
import numpy as np

from luma.oled.device import sh1106
import RPi.GPIO as GPIO

import time
import subprocess
import pygame

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# GPIO define
RST_PIN = 25
CS_PIN = 8
DC_PIN = 24
KEY_UP_PIN = 6
KEY_DOWN_PIN = 19
KEY_LEFT_PIN = 5
KEY_RIGHT_PIN = 26
KEY_PRESS_PIN = 13
KEY1_PIN = 21
KEY2_PIN = 20
KEY3_PIN = 16

# Load default font.
# font=ImageFont.load_default()
# print(font.getmask(""))
# print(font.getsize("hello"))

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = 128
height = 64
image = Image.new('1', (width, height))

# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height - padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

RST = 25
CS = 8
DC = 24

USER_I2C = 0

if USER_I2C == 1:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RST, GPIO.OUT)
    GPIO.output(RST, GPIO.HIGH)

    serial = i2c(port=1, address=0x3c)
else:
    serial = spi(device=0, port=0, bus_speed_hz=8000000, transfer_size=4096, gpio_DC=24, gpio_RST=25)

device = sh1106(serial, rotate=2)  # sh1106
# init GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(KEY_UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY_DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY_LEFT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY_RIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY_PRESS_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up

playList = []
playing = 0

PAGE_SIZE = 5
ITEM_H = device.height / 5
ITEM_W = device.width / 2
STAT_DIR = 0
STAT_FILE = 1
ROOT_PATH = "/home/pi/screen/"

# path = "/home/pi/Music/"

isUp = False
isDown = False
isLeft = False
isRight = False
isPin = False
isKey1 = False
isKey2 = False
isKey3 = False
isPause = False

# pygame.mixer.init()
pygame.init()
font = ImageFont.truetype("/home/pi/screen/HeiTi-2.ttc", 10)
font_welcome = ImageFont.truetype("/home/pi/screen/HeiTi-2.ttc", 15)


def playMusic(path):
    pygame.mixer.music.stop()
    track = pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    print(path + " is playing.")


def onDown(list, current, page):
    if (page + 1) * 5 >= len(list):
        if current + 1 >= 5 - (page + 1) * 5 + len(list):
            page = 0
            current = 0
            return current, page

    if current + 1 >= 5:
        current = 0
        page += 1
        return current, page

    # if current + 1 >= 5:
    #     current = 0
    #     if page * 5 < len(list):
    #         page += 1
    #     else:
    #         page = 0
    #     return current, page

    current += 1
    return current, page


def onUp(list, current, page):
    if current - 1 < 0:
        if page > 0:
            current = 4
            page -= 1
        else:
            current = 0
            page = len(list) / 5 if len(list) % 5 != 0 else (len(list) / 5 - 1 if len(list) != 0 else 0)
        return current, page

    current -= 1
    return current, page


def onPin(path, list, current, page):
    # pygame.mixer.music.stop()
    playList = []
    # first=True
    now = path + list[page * 5 + current]
    for name in list[page * 5 + current + 1:]:
        playList.append(path + name)

    playMusic(now)
    np.random.shuffle(playList)
    return playList


def onStop():
    pygame.mixer.music.stop()


def updateFileList(path):
    cmd = 'ls "' + path + '" | grep .mp3'
    if subprocess.call(cmd + " > log", shell=True) == 0:
        List1 = subprocess.check_output(cmd, shell=True)
    else:
        List1 = ""
    listFile = str(List1).split("\n")
    listFile.remove('')
    return listFile


def updateDirList(path):
    cmd = 'ls "' + path + '" -F | grep "/$"'
    if subprocess.call(cmd + " > log", shell=True) == 0:
        List2 = subprocess.check_output(cmd, shell=True)
    else:
        List2 = ""
    listDir = str(List2).split("/\n")
    listDir.remove('')
    return listDir


def getAllMusic(path):
    cmd = 'find "' + path + '" -name "*.mp3"'
    if subprocess.call(cmd + " > log", shell=True) == 0:
        List1 = subprocess.check_output(cmd, shell=True)
    else:
        List1 = ""
    listFile = str(List1).split("\n")
    listFile.remove('')
    return listFile


listAllFiles = getAllMusic("/home") + getAllMusic("/media") + getAllMusic("/usr")


# try:
def onDrawWelcome():
    t = 0
    img = Image.open(ROOT_PATH + "img/parrot.png")
    img = img.resize((50, 50))
    while t < 200:
        t += 1
        with canvas(device) as draw:
            draw.text((40, ITEM_H * 2.5), unicode("GLOOMY", 'UTF-8'), font=font_welcome, fill="white")
            draw.bitmap((x, ITEM_H), img, fill="white")


def onDrawStart():
    imgNote = Image.open(ROOT_PATH + "img/music_note.ico").resize((32, 32))
    imgFolder = Image.open(ROOT_PATH + "img/folder_music.ico").resize((39, 32))
    STAT_ALL = 0
    STAT_FOLDER = 1
    status = STAT_ALL
    global isDown
    global isKey1
    global isKey2
    global isKey3
    global isPause
    global isPin
    global isUp
    global isLeft
    global isRight
    global playList
    global playing
    while True:
        with canvas(device) as draw:
            if (not GPIO.input(KEY_LEFT_PIN)) and isLeft is False:
                # step-=1
                isLeft = True
                if status == STAT_FOLDER:
                    status = STAT_ALL

            elif GPIO.input(KEY_LEFT_PIN):
                isLeft = False

            if (not GPIO.input(KEY_RIGHT_PIN)) and isRight is False:
                # step-=1
                isRight = True
                if status == STAT_ALL:
                    status = STAT_FOLDER

            elif GPIO.input(KEY_RIGHT_PIN):
                isRight = False

            if (not GPIO.input(KEY_PRESS_PIN)) and isPin is False:
                # os.system("sudo halt")
                isPin = True
                if status == STAT_ALL:
                    onDrawMusicInterface()
                elif status == STAT_FOLDER:
                    onDrawFileInterface("/")

            elif GPIO.input(KEY_PRESS_PIN):
                isPin = False

            if (not GPIO.input(KEY2_PIN)) and (isKey2 == False):
                if not isPause:
                    pygame.mixer.music.pause()
                    isPause = True
                else:
                    pygame.mixer.music.unpause()
                    isPause = False
                isKey2 = True
            elif GPIO.input(KEY2_PIN):
                isKey2 = False

            if (not pygame.mixer.music.get_busy()) and len(playList) > 0 and (isPause == False):
                if playing + 1 < len(playList):
                    playing += 1
                elif playing + 1 == len(playList):
                    np.random.shuffle(playList)
                    playing = 0
                # playing = np.random.randint(0, len(playList))
                playMusic(playList[playing])

            draw.rectangle([(x + status * (ITEM_W - 5), top + 10), (x + status * (ITEM_W - 5) + ITEM_W, bottom - 10)],
                           outline="white")
            draw.bitmap((x + 10, ITEM_H), imgNote, fill="white")
            draw.bitmap((x + ITEM_W + 10, ITEM_H), imgFolder, fill="white")


def onDrawMusicInterface():
    current = 0
    page = 0
    global isDown
    global isKey1
    global isKey2
    global isKey3
    global isPause
    global isPin
    global isUp
    global isLeft
    global isRight
    global playList
    global playing

    listFile = listAllFiles

    while True:
        with canvas(device) as draw:

            # draw.rectangle(device.bounding_box, outline="white", fill="black")
            # draw.text((30, 40), "Hello World", fill="white")
            # Shell scripts for system monitoring from here :
            # https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load

            # Write two lines of text.
            if (not GPIO.input(KEY_DOWN_PIN)) and isDown == False:  # button is released
                # step+=1 #down
                isDown = True
                current, page = onDown(listFile, current, page)
            elif GPIO.input(KEY_DOWN_PIN):
                isDown = False

            if (not GPIO.input(KEY_UP_PIN)) and isUp == False:
                # step-=1
                isUp = True
                current, page = onUp(listFile, current, page)
            elif GPIO.input(KEY_UP_PIN):
                isUp = False

            if (not GPIO.input(KEY_LEFT_PIN)) and isLeft is False:
                # step-=1
                isLeft = True

            elif GPIO.input(KEY_LEFT_PIN):
                isLeft = False

            if (not GPIO.input(KEY_RIGHT_PIN)) and isRight is False:
                # step-=1
                isRight = True

            elif GPIO.input(KEY_RIGHT_PIN):
                isRight = False

            if (not GPIO.input(KEY_PRESS_PIN)) and isPin is False:
                # os.system("sudo halt")
                isPin = True
                now = listFile[current + page * 5]
                playList = listFile[:]
                playMusic(now)
                np.random.shuffle(playList)
                playing = 0
                isPause = False
            elif GPIO.input(KEY_PRESS_PIN):
                isPin = False

            if (not GPIO.input(KEY1_PIN)) and isKey1 == False:
                # path = path + "../"
                isKey1 = True
                return
            elif GPIO.input(KEY1_PIN):
                isKey1 = False

            if (not GPIO.input(KEY2_PIN)) and (isKey2 == False):
                if not isPause:
                    pygame.mixer.music.pause()
                    isPause = True
                else:
                    pygame.mixer.music.unpause()
                    isPause = False
                isKey2 = True
            elif GPIO.input(KEY2_PIN):
                isKey2 = False

            # if (not GPIO.input(KEY3_PIN)) and (isKey3 == False):
            #     isKey3 = True
            #     onDraw(path + list[page * 5 + current] + "/")
            #     # current = 0
            #     # page = 0
            # elif GPIO.input(KEY3_PIN):
            #     isKey3 = False

            if (not pygame.mixer.music.get_busy()) and len(playList) > 0 and (isPause == False):
                if playing + 1 < len(playList):
                    playing += 1
                elif playing + 1 == len(playList):
                    np.random.shuffle(playList)
                    playing = 0
                # playing = np.random.randint(0, len(playList))
                playMusic(playList[playing])

            # draw.text((x,top-step), str(List), font=font, fill="white")
            if page * 5 + 4 < len(listFile):
                endFile = page * 5 + 5
                lastNumFile = 5
            else:
                endFile = len(listFile)
                lastNumFile = len(listFile) - page * 5

            for i, name in zip(range(lastNumFile), listFile[page * 5:endFile]):
                h = i * ITEM_H
                if i == current:
                    draw.rectangle([(0, top + h), (ITEM_W * 2, top + h + 10)], outline="white")

                lastName = name.split("/")[-1]
                draw.text((x, top + h), unicode(lastName, 'UTF-8'), font=font, fill="white")


def onDrawFileInterface(path):
    status = STAT_DIR
    currentDir = 0
    pageDir = 0
    current = 0
    page = 0
    global isDown
    global isKey1
    global isKey2
    global isKey3
    global isPause
    global isPin
    global isUp
    global isLeft
    global isRight
    global playList
    global playing

    listDir = updateDirList(path)
    listFile = []
    if len(listDir) > 0:
        listFile = updateFileList(path + listDir[0])

    while True:
        with canvas(device) as draw:

            # draw.rectangle(device.bounding_box, outline="white", fill="black")
            # draw.text((30, 40), "Hello World", fill="white")
            # Shell scripts for system monitoring from here :
            # https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load

            # Write two lines of text.
            if (not GPIO.input(KEY_DOWN_PIN)) and isDown == False:  # button is released
                # step+=1 #down
                isDown = True
                if status == STAT_FILE:
                    current, page = onDown(listFile, current, page)
                elif status == STAT_DIR:
                    currentDir, pageDir = onDown(listDir, currentDir, pageDir)
                    listFile = updateFileList(path + listDir[pageDir * 5 + currentDir])
            elif GPIO.input(KEY_DOWN_PIN):
                isDown = False

            if (not GPIO.input(KEY_UP_PIN)) and isUp == False:
                # step-=1
                isUp = True
                if status == STAT_FILE:
                    current, page = onUp(listFile, current, page)
                elif status == STAT_DIR:
                    currentDir, pageDir = onUp(listDir, currentDir, pageDir)
                    listFile = updateFileList(path + listDir[pageDir * 5 + currentDir])
            elif GPIO.input(KEY_UP_PIN):
                isUp = False

            if (not GPIO.input(KEY_LEFT_PIN)) and isLeft is False:
                # step-=1
                isLeft = True
                if status == STAT_DIR:
                    status = STAT_FILE

            elif GPIO.input(KEY_LEFT_PIN):
                isLeft = False

            if (not GPIO.input(KEY_RIGHT_PIN)) and isRight is False:
                # step-=1
                isRight = True
                if status == STAT_FILE:
                    status = STAT_DIR

            elif GPIO.input(KEY_RIGHT_PIN):
                isRight = False

            if (not GPIO.input(KEY_PRESS_PIN)) and isPin is False:
                # os.system("sudo halt")
                isPin = True
                if status == STAT_FILE:
                    playList = onPin(path + listDir[pageDir * 5 + currentDir] + "/", listFile, current, page)
                    playing = 0
                    isPause = False
                elif status == STAT_DIR:
                    onDrawFileInterface(path + listDir[pageDir * 5 + currentDir] + "/")
            elif GPIO.input(KEY_PRESS_PIN):
                isPin = False

            if (not GPIO.input(KEY1_PIN)) and isKey1 == False:
                # path = path + "../"
                isKey1 = True
                return
                # if path != "/":
                #     return
                # onDraw(path + "../")
                # current = 0
                # page = 0
            elif GPIO.input(KEY1_PIN):
                isKey1 = False

            if (not GPIO.input(KEY2_PIN)) and (isKey2 == False):
                # playMusic(path+list[page*5+current])
                # os.system('play "'+path+list[step/8]+'"')
                if not isPause:
                    pygame.mixer.music.pause()
                    isPause = True
                else:
                    pygame.mixer.music.unpause()
                    isPause = False
                isKey2 = True
            elif GPIO.input(KEY2_PIN):
                isKey2 = False

            # if (not GPIO.input(KEY3_PIN)) and (isKey3 == False):
            #     isKey3 = True
            #     onDraw(path + list[page * 5 + current] + "/")
            #     # current = 0
            #     # page = 0
            # elif GPIO.input(KEY3_PIN):
            #     isKey3 = False

            if (not pygame.mixer.music.get_busy()) and len(playList) > 0 and (isPause == False):
                if playing + 1 < len(playList):
                    playing += 1
                elif playing + 1 == len(playList):
                    np.random.shuffle(playList)
                    playing = 0
                # playing = np.random.randint(0, len(playList))
                playMusic(playList[playing])

            # draw.text((x,top-step), str(List), font=font, fill="white")
            if page * 5 + 4 < len(listFile):
                endFile = page * 5 + 5
                lastNumFile = 5
            else:
                endFile = len(listFile)
                lastNumFile = len(listFile) - page * 5

            if pageDir * 5 + 4 < len(listDir):
                endDir = pageDir * 5 + 5
                lastNumDir = 5
            else:
                endDir = len(listDir)
                lastNumDir = len(listDir) - pageDir * 5

            for i, name in zip(range(lastNumFile), listFile[page * 5:endFile]):
                h = i * ITEM_H
                if i == current:
                    draw.rectangle([(0, top + h), (ITEM_W, top + h + 10)], outline="white")

                draw.text((x, top + h), unicode(name, 'UTF-8'), font=font, fill="white")

            draw.rectangle([(ITEM_W, top), (ITEM_W * 2, bottom)], outline="white", fill="black")

            for i, name in zip(range(lastNumDir), listDir[pageDir * 5:endDir]):
                h = i * ITEM_H
                if i == currentDir:
                    draw.rectangle([(ITEM_W, top + h), (ITEM_W * 2, top + h + 10)], outline="white")

                draw.text((x + ITEM_W, top + h), unicode(name, 'UTF-8'), font=font, fill="white")


# except:
#     print("except")
onDrawWelcome()
onDrawStart()
GPIO.cleanup()
