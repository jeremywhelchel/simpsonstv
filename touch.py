#!/usr/bin/python3

import evdev
import logging
import socket

# This is oddly swapped. X is actually the long dimension on the physical screen.
MAX_X = 480
MAX_Y = 640

# Defines left/right touch area
X_MARGIN = 100

# How far to seek fwd/back
SEEK_SECS = 30

# Must match MPV's --input-ipc-server flag
SOCKET_PATH = "/tmp/mpvsocket"


def SendMPV(msg: str):
    logging.info("MPV command: %s", msg)
    msg += "\n"
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(SOCKET_PATH)
    sent = client.send(msg.encode())
    response = client.recv(4096)
    logging.info(f"Received response: {response.decode().strip()}")
    client.close()


# Commands here: https://mpv.io/manual/master/#json-ipc
def Act(x: int, y: int, delta_x: int, delta_y: int):
    # Swipe left
    if delta_x < -(MAX_X / 2):
        SendMPV("playlist-prev")
    # Swipe right
    elif delta_x > MAX_X / 2:
        SendMPV("playlist-next")
    # Left touch
    elif x < X_MARGIN:
        SendMPV(f"seek {0-SEEK_SECS}")
    # Middle touch
    elif x > MAX_X - X_MARGIN:
        SendMPV(f"seek {SEEK_SECS}")
    # Right touch
    else:
        SendMPV("cycle pause")


def main():
    logging.getLogger().setLevel(logging.INFO)
    device = evdev.InputDevice("/dev/input/event0")
    logging.info("Input device: %s", device)

    # Key event comes before location event. So assume first key down is in middle of screen
    x = int(MAX_X / 2)
    y = int(MAX_Y / 2)

    down_x = None
    down_y = None

    for event in device.read_loop():
        if event.type == evdev.ecodes.EV_KEY:
            if event.code == evdev.ecodes.BTN_TOUCH:
                if event.value == 0x0:
                    delta_x = x - down_x
                    delta_y = y - down_y
                    Act(x, y, delta_x, delta_y)
                if event.value == 0x1:
                    down_x = x
                    down_y = y
        elif event.type == evdev.ecodes.EV_ABS:
            # Screen is rotated, so X & Y are swapped from how the input reports them.
            if event.code == evdev.ecodes.ABS_MT_POSITION_X:
                y = MAX_Y - event.value
            elif event.code == evdev.ecodes.ABS_MT_POSITION_Y:
                x = MAX_X - event.value


main()
