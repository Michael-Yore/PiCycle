#!/usr/bin/env python3

import time
import threading
from datetime import datetime, timedelta
from sense_hat import SenseHat

sense = SenseHat()
sense.clear()


GREEN  = (0,   200, 0  )
RED    = (200, 0,   0  )
BLUE   = (0,   100, 255)
WHITE  = (200, 200, 200)
OFF    = (0,   0,   0  )


journey_active    = False
journey_start     = None
journey_log       = []   # list of (start_datetime, duration_timedelta)
current_view      = "idle"   # idle | recording | review
review_index      = 0
stop_ticker       = threading.Event()

def format_duration(td):
    """Format a timedelta as HH:MM:SS string."""
    total_seconds = int(td.total_seconds())
    hours   = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours > 0:
        return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
    else:
        return "{:02d}:{:02d}".format(minutes, seconds)


def format_start(dt):
    """Format a start datetime as a short readable string."""
    return dt.strftime("%H:%M")


def scroll_text(text, colour, bg=(0, 0, 0), speed=0.06):
    """Scroll text across the LED matrix then clear."""
    sense.show_message(
        text,
        scroll_speed=speed,
        text_colour=colour,
        back_colour=bg,
    )


def led_solid(colour):
    sense.set_pixels([colour] * 64)



def live_ticker():
    """
    While a journey is active, scroll the elapsed time on the LED
    every 10 seconds so the rider can glance at it.
    Runs in a background thread.
    """
    while not stop_ticker.is_set():
        if journey_active and journey_start:
            elapsed = datetime.now() - journey_start
            text = format_duration(elapsed)
            sense.show_message(
                text,
                scroll_speed=0.05,
                text_colour=WHITE,
                back_colour=(80, 0, 0),
            )
            # After scrolling, restore solid red
            if journey_active:
                led_solid(RED)
        stop_ticker.wait(timeout=10)



def start_journey():
    global journey_active, journey_start, current_view
    journey_active = True
    journey_start  = datetime.now()
    current_view   = "recording"

    stop_ticker.clear()
    t = threading.Thread(target=live_ticker, daemon=True)
    t.start()

    led_solid(RED)
    print("Journey started at {}".format(journey_start.strftime("%H:%M:%S")))


def stop_journey():
    global journey_active, journey_start, current_view, review_index

    stop_ticker.set()
    journey_active = False
    current_view   = "review"

    end_time = datetime.now()
    duration = end_time - journey_start
    journey_log.append((journey_start, duration))
    review_index = len(journey_log) - 1

    print("Journey stopped. Duration: {}".format(format_duration(duration)))

    # Display the result
    display_journey(review_index)


def display_journey(index):
    """Scroll the journey time for the given log index."""
    if not journey_log:
        scroll_text("No journeys", WHITE)
        return

    start_dt, duration = journey_log[index]
    text = "Journey {}  Started {}  Time {}".format(
        index + 1,
        format_start(start_dt),
        format_duration(duration),
    )
    scroll_text(text, list(BLUE))
    led_solid(OFF)



def show_idle():
    """Show a green ready screen with a small arrow indicator."""
    global current_view
    current_view = "idle"
    led_solid(GREEN)
    print("Ready. Press joystick centre to start a journey.")



def handle_joystick(event):
    global current_view, review_index

    if event.action != "pressed":
        return

    if event.direction == "middle":
        if current_view == "idle":
            start_journey()

        elif current_view == "recording":
            stop_journey()

        elif current_view == "review":
            # Press middle again to go back to idle ready state
            show_idle()

    elif event.direction == "up" and current_view == "review":
        # Scroll to newer journey
        if review_index < len(journey_log) - 1:
            review_index += 1
            display_journey(review_index)

    elif event.direction == "down" and current_view == "review":
        # Scroll to older journey
        if review_index > 0:
            review_index -= 1
            display_journey(review_index)

    elif event.direction == "left":
        # Always go back to idle from any state
        if current_view == "recording":
            stop_journey()
        show_idle()


def main():
    print("=" * 45)
    print(" Sense HAT Journey Logger")
    print("=" * 45)
    print("  Joystick MIDDLE  - Start / Stop journey")
    print("  Joystick UP/DOWN - Browse past journeys")
    print("  Joystick LEFT    - Return to idle")
    print("  Ctrl+C           - Quit")
    print("=" * 45)

    show_idle()

    try:
        while True:
            for event in sense.stick.get_events():
                handle_joystick(event)
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nJourney Logger stopped.")
        if journey_log:
            print("\nJourney Summary:")
            print("-" * 35)
            for i, (start_dt, duration) in enumerate(journey_log):
                print("  Journey {}  {}  Duration: {}".format(
                    i + 1,
                    start_dt.strftime("%Y-%m-%d %H:%M"),
                    format_duration(duration),
                ))
        sense.clear()


if __name__ == "__main__":
    main()
