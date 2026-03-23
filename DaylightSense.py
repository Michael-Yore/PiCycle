#!/usr/bin/env python3
import time
import math
from sense_hat import SenseHat
 
SAMPLE_INTERVAL   = 0.3   # seconds between updates
SMOOTHING_SAMPLES = 5     # rolling average window size
 
GLOW_COLOUR = (255, 220, 180)
 
sense = SenseHat()
sense.low_light = False
 
def read_clear():
    try:
        # Sense HAT V2
        r, g, b, clear = sense.colour.colour
        return clear
    except AttributeError:
        pass
 
    try:
        # Some builds expose get_color()
        r, g, b = sense.get_color()[:3]
        return (r + g + b) // 3
    except Exception:
        pass
 
    # Last resort: use the colour property directly
    colour = sense.colour
    return int((colour.red + colour.green + colour.blue) / 3)
 
 
 
def calibrate():
    print("Calibrating - please keep the room at its CURRENT brightness...")
 
    # Flash blue to signal calibration
    sense.clear(0, 0, 128)
    time.sleep(0.5)
    sense.clear()
 
    readings = []
    for i in range(15):
        readings.append(read_clear())
        time.sleep(0.2)
 
    ambient = sum(readings) / len(readings)
    print(f"  Ambient clear value: {ambient:.1f} / 255")
 
    # Set dark threshold well below ambient and bright threshold at/above ambient
    dark_thresh   = max(0,   ambient * 0.3)   # 30% of current = dark
    bright_thresh = min(255, ambient * 1.2)   # 120% of current = bright
 
    # Safety: ensure a minimum spread so the mapping is not flat
    if bright_thresh - dark_thresh < 20:
        dark_thresh   = max(0,   ambient - 30)
        bright_thresh = min(255, ambient + 30)
 
    print(f"  Dark threshold  : {dark_thresh:.1f}")
    print(f"  Bright threshold: {bright_thresh:.1f}")
 
    # Flash green to signal calibration done
    sense.clear(0, 128, 0)
    time.sleep(0.5)
    sense.clear()
 
    return dark_thresh, bright_thresh
 
 
 
def clear_to_brightness(clear_val, dark_thresh, bright_thresh):
    clamped = max(dark_thresh, min(bright_thresh, clear_val))
 
    span = bright_thresh - dark_thresh
    if span == 0:
        normalised = 0.5
    else:
        normalised = (clamped - dark_thresh) / span
 
    # Invert: bright room -> 0.0, dark room -> 1.0
    inverted = 1.0 - normalised
 
    # Square-root gamma for a smooth, natural curve
    curved = math.sqrt(inverted)
 
    return int(round(curved * 255))
 
 
 
def make_pixel(brightness):
    factor = brightness / 255.0
    return tuple(int(c * factor) for c in GLOW_COLOUR)
 
 
 
def main():
    print("=" * 50)
    print(" Sense HAT Daylight Sensor")
    print("=" * 50)
 
    dark_thresh, bright_thresh = calibrate()
 
    print("\nRunning. Press Ctrl+C to stop.")
    print(f"{'Clear':>8}  {'Brightness':>10}  {'Pixel':>20}")
    print("-" * 45)
 
    buffer = []
    last_brightness = -1
 
    try:
        while True:
            raw = read_clear()
 
            # Rolling average
            buffer.append(raw)
            if len(buffer) > SMOOTHING_SAMPLES:
                buffer.pop(0)
            avg = sum(buffer) / len(buffer)
 
            brightness = clear_to_brightness(avg, dark_thresh, bright_thresh)
            pixel = make_pixel(brightness)
 
            if brightness != last_brightness:
                sense.set_pixels([pixel] * 64)
                last_brightness = brightness
                print(f"{avg:8.1f}  {brightness:10d}  {str(pixel):>20}")
 
            time.sleep(SAMPLE_INTERVAL)
 
    except KeyboardInterrupt:
        sense.clear()
        print("\nDaylight sensor stopped.")
 
 
if __name__ == "__main__":
    main()
