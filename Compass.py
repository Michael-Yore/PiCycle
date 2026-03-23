from sense_hat import SenseHat
from time import sleep

sense = SenseHat()

R = (255, 0, 0)
W = (255, 255, 255)
O = (0, 0, 0)

compass1 = [
    W, W, W, R, R, W, W, W,
    W, W, W, R, R, W, W, W,
    W, W, W, R, R, W, W, W,
    W, W, W, R, R, W, W, W,
    W, W, W, O, O, W, W, W,
    W, W, W, O, O, W, W, W,
    W, W, W, O, O, W, W, W,
    W, W, W, O, O, W, W, W
]

compass2 = [
    W, W, W, W, W, W, R, R,
    W, W, W, W, W, R, R, R,
    W, W, W, W, R, R, R, W,
    W, W, W, W, R, R, W, W,
    W, W, O, O, W, W, W, W,
    W, O, O, O, W, W, W, W,
    O, O, O, W, W, W, W, W,
    O, O, W, W, W, W, W, W
]

compass3 = [
    W, W, W, W, W, W, W, W,
    W, W, W, W, W, W, W, W,
    W, W, W, W, W, W, W, W,
    O, O, O, O, R, R, R, R,
    O, O, O, O, R, R, R, R,
    W, W, W, W, W, W, W, W,
    W, W, W, W, W, W, W, W,
    W, W, W, W, W, W, W, W,
]

compass4 = [
    O, O, W, W, W, W, W, W,
    O, O, O, W, W, W, W, W,
    W, O, O, O, W, W, W, W,
    W, W, O, O, W, W, W, W,
    W, W, W, W, R, R, W, W,
    W, W, W, W, R, R, R, W,
    W, W, W, W, W, R, R, R,
    W, W, W, W, W, W, R, R
]

compass5 = [
    W, W, W, O, O, W, W, W,
    W, W, W, O, O, W, W, W,
    W, W, W, O, O, W, W, W,
    W, W, W, O, O, W, W, W,
    W, W, W, R, R, W, W, W,
    W, W, W, R, R, W, W, W,
    W, W, W, R, R, W, W, W,
    W, W, W, R, R, W, W, W
]

compass6 = [
    W, W, W, W, W, W, O, O,
    W, W, W, W, W, O, O, O,
    W, W, W, W, O, O, O, W,
    W, W, W, W, O, O, W, W,
    W, W, R, R, W, W, W, W,
    W, R, R, R, W, W, W, W,
    R, R, R, W, W, W, W, W,
    R, R, W, W, W, W, W, W
]

compass7 = [
    W, W, W, W, W, W, W, W,
    W, W, W, W, W, W, W, W,
    W, W, W, W, W, W, W, W,
    R, R, R, R, O, O, O, O,
    R, R, R, R, O, O, O, O,
    W, W, W, W, W, W, W, W,
    W, W, W, W, W, W, W, W,
    W, W, W, W, W, W, W, W
]

compass8 = [
    R, R, W, W, W, W, W, W,
    R, R, R, W, W, W, W, W,
    W, R, R, R, W, W, W, W,
    W, W, R, R, W, W, W, W,
    W, W, W, W, O, O, W, W,
    W, W, W, W, O, O, O, W,
    W, W, W, W, W, O, O, O,
    W, W, W, W, W, W, O, O
]

while True:
    #sleep(0.5)
    degrees = sense.get_compass()
    direction = round(degrees)
    if degrees<45:
        sense.set_pixels(compass2)  #2  #8
    elif degrees<90:
        sense.set_pixels(compass1)  #1  #7
    elif degrees<135:
        sense.set_pixels(compass8)  #8  #6
    elif degrees<180:
        sense.set_pixels(compass7)  #7  #5
    elif degrees<225:
        sense.set_pixels(compass6)  #6  #4
    elif degrees<270:
        sense.set_pixels(compass5)  #5  #3
    elif degrees<315:
        sense.set_pixels(compass4)  #4  #2
    elif degrees<360:
        sense.set_pixels(compass3)  #3  #1
    
