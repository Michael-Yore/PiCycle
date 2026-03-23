#!/usr/bin/env python3
from sense_hat import SenseHat
from picamera2 import Picamera2, Preview
from time import sleep
import subprocess
import sys
import os

sense = SenseHat()
sense.clear()

R = (255,0,0)       #Red
G = (0, 255, 0)     #Green
B = (0, 0, 255)     #Blue
O = (0, 0, 0)       #Off/Black
W = (255, 255, 255) #White
Y = (255, 255, 0)   #Yellow
P = (255, 255, 214) #Peach
T = (23, 248, 182)  #Tan
DT = (15, 255, 163) #Dark Tan


sunIcon = [                     #icon for daylight sensor
    O, O, O, O, O, O, O, O,
    O, O, O, Y, Y, O, O, O,
    O, O, Y, Y, Y, Y, O, O,
    O, Y, Y, Y, Y, Y, Y, O,
    O, Y, Y, Y, Y, Y, Y, O,
    O, O, Y, Y, Y, Y, O, O,
    O, O, O, Y, Y, O, O, O,
    O, O, O, O, O, O, O, O
]

compassIcon = [                 #icon for compass
    W, W, W, W, W, W, W, W,
    W, W, W, W, W, R, R, W,
    W, W, W, W, R, R, R, W,
    W, W, W, R, R, R, W, W,
    W, W, O, O, R, W, W, W,
    W, O, O, O, W, W, W, W,
    W, O, O, W, W, W, W, W,
    W, W, W, W, W, W, W, W
]

thermIcon = [                   #icon for thermometer
    O, O, O, W, W, O, O, O,
    O, O, W, R, W, W, O, O,
    O, O, W, R, R, W, O, O,
    O, O, W, R, W, W, O, O,
    O, O, W, R, R, W, O, O,
    O, O, W, R, W, W, O, O,
    O, O, W, R, R, W, O, O,
    O, O, W, W, W, W, O, O
]

dropIcon = [                    #icon for humidity/pressure
    O, O, O, O, O, O, O, O,
    O, O, O, O, B, O, O, O,
    O, O, O, B, B, O, O, O,
    O, O, B, B, B, B, O, O,
    O, B, B, B, W, B, B, O,
    O, B, B, B, B, B, B, O,
    O, O, B, B, B, B, B, O,
    O, O, O, O, O, O, O, O
]

moonIcon = [                    #icon for shutdown
    O, O, O, O, O, O, O, O,
    O, O, O, P, O, O, O, O,
    O, O, O, O, P, O, O, O,
    O, O, O, O, O, P, O, O,
    O, O, O, O, O, P, O, O,
    O, O, O, O, P, O, O, O,
    O, O, O, P, O, O, O, O,
    O, O, O, O, O, O, O, O
]

mapIcon = [                     #icon for logger
    O, O, T, T, O, O, O, O,
    O, DT, T, T, DT, O, T, O,
    O, DT, T, R, R, DT, T, O,
    O, R, R, T, DT, R, T, O,
    O, DT, T, T, DT, DT, R, O,
    O, DT, O, T, DT, DT, T, O,
    O, O, O, O, DT, DT, O, O,
    O, O, O, O, O, O, O, O
]

timeIcon = [                    #icon for timelapse
    O, W, W, W, W, W, W, O,
    O, W, W, W, W, W, W, O,
    O, O, W, R, R, W, O, O,
    O, O, O, W, W, O, O, O,
    O, O, O, W, W, O, O, O,
    O, O, W, R, R, W, O, O,
    O, W, R, R, R, R, W, O,
    O, W, W, W, W, W, W, O
]

camIcon = [                     #icon for dashcam
    W, W, W, W, W, W, W, W,
    W, W, W, W, W, W, W, W,
    W, W, O, O, O, W, O, W,
    O, O, O, O, O, O, O, O,
    O, O, W, W, W, O, W, O,
    O, O, W, O, W, O, O, O,
    O, O, W, W, W, O, O, O,
    O, O, O, O, O, O, O, O
]

off = [
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O,
    O, O, O, O, O, O, O, O
]


menuIcons = [thermIcon, compassIcon, mapIcon, dropIcon, sunIcon, timeIcon, camIcon, moonIcon]
speed = 0.05        #scroll speed
timelapseFreq = 10  #how often to take photo for timelapse

process = None

def main():
    numOptions = 8
    max = numOptions-1
    min = 0
    curr = 0
    while True:
        sense.set_pixels(menuIcons[curr])   #display current option icon
        event = sense.stick.wait_for_event()
        if event.action == 'pressed' and event.direction == 'right':
            curr+=1
        elif event.action == 'pressed' and event.direction == 'left':
            curr-=1
        if curr < 0:
            curr = max
        elif curr > max:
            curr = min

        sense.set_pixels(menuIcons[curr])   #display current option icon
        if event.action == 'pressed' and event.direction == 'middle':  #if middle button is pressed
            sense.clear()
            #case/if statements to run each function
            match curr:
                case 0:
                    tempSense()                                                     #temperature
                    break
                case 1:
                   run_with_cancel(["python3", "./Compass.py"])                      #compass
                case 2:
                    logJourney()                                                    #journeyLogger
                case 3:
                    humiditySense()                                                 #humidity
                case 4:
                    daylightSense()                                                 #daylight
                case 5:
                    timelapseStart()                                                #timelapse
                case 6:
                    dashcamStart()                                                  #dashcam
                case 7:
                    shutdown()
                case _:
                    #default case
                    print("")

def tempSense():
    print("Reading Temp!")
    temp = sense.get_temperature()   #read temp from pressure sensor
    tempRounded = round(temp)                    #round temp reading

    #print relevant advice based on temperature reading
    #message = "Temperature: " + str(tempRounded) + "C"
    #sense.show_message(message, scroll_speed=speed)
    if 10<=tempRounded<=20:
        sense.show_message("Perfect temperature for cycling!", text_colour=G, scroll_speed=speed)
    elif 2<tempRounded<10:
        sense.show_message("It's chilly, bundle up!", text_colour=R, scroll_speed=speed)
    elif tempRounded<2:
        sense.show_message("Freezing temperatures, exercise caution", text_colour=R, scroll_speed=speed)
    elif tempRounded>20:
        sense.show_message("It's hot, stay hydrated and take breaks", text_colour=R, scroll_speed=speed)
    sleep(1)
    return

def logJourney():
   run_with_cancel(["python3", "./Logger.py"])
   return

def humiditySense():
    humidity = sense.get_humidity()                 #read humidity in % relative humidity
    pressure = sense.get_pressure()                 #read pressure in pascals

    if 70<=humidity<90:
        sense.show_message("Overcast", scroll_speed=speed)
    elif humidity>=90:
        sense.show_message("Precipitation likely", scroll_speed=speed)
    else:
        sense.show_message("Low Humidity", scroll_speed=speed)
    sleep(1)

    if pressure<100000:
        sense.show_message("Low Pressure, unstable conditions, possible rain", scroll_speed=speed)
    elif pressure>102000:
        sense.show_message("High Pressure, settled conditions, stable and fair", scroll_speed=speed)
    else:
        sense.show_message("Normal Pressure", scroll_speed=speed)
    sleep(1)
    return

def daylightSense():
    run_with_cancel(["python3", "./DaylightSense.py"]) 
    return

def timelapseStart():
    sense.clear()
    picam2 = Picamera2()
    camera_config = picam2.create_preview_configuration()
    picam2.configure(camera_config)

    picam2.start()
    sleep(2)
    curr = 0
    while True:
        for e in sense.stick.get_events():
            if e.action == 'pressed' and e.direction == 'middle':
                picam2.stop()
                return
        sense.set_pixels(timeIcon)
        name = "/home/igneus/timelapse/frame" + str(curr) + ".jpg"
        picam2.capture_file(name)
        curr+=1
        sense.clear()
        sleep(int(timelapseFreq))

def dashcamStart():
    run_with_cancel(["python3", "./Dashcam.py"])
    return

def run_with_cancel(command):
    global process
    process = subprocess.Popen(command)

    while True:
        for e in sense.stick.get_events():
            if e.action == 'pressed' and e.direction == 'up':
                process.terminate()
                process.wait()
                return

def shutdown():
    print("Powering down...")

    for i in range(5):
        sense.low_light = True
        sleep(0.2)
    
    sense.clear()
    sleep(1)

    os.system("sudo shutdown -h now")
    sys.exit()


if __name__ == "__main__":
    main()

