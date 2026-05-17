#!/usr/bin/env python3
import time

import hid


VID = 0x2B77
PID = 0x3661


def open_interfaces():
    devices = {}
    for desc in hid.enumerate(VID, PID):
        usage = desc.get("usage", 0)
        dev = hid.device()
        dev.open_path(desc["path"])
        if usage == 0x101:
            devices["keyboard"] = dev
        elif usage == 0x102:
            devices["mouse"] = dev
        elif usage == 0x103:
            devices["touch"] = dev
        else:
            dev.close()
    return devices


def send_key(dev, code):
    dev.write([0, 0, 0, code, 0, 0, 0, 0, 0])
    time.sleep(0.05)
    dev.write([0, 0, 0, 0, 0, 0, 0, 0, 0])
    time.sleep(0.1)


def main():
    devices = open_interfaces()
    print("AgentKVM2USB interfaces:", sorted(devices))

    keyboard = devices.get("keyboard")
    if keyboard:
        for code in (0x18, 0x16, 0x05):  # u, s, b
            send_key(keyboard, code)
        print("sent keyboard sequence: usb")

    touch = devices.get("touch")
    if touch:
        x = int(0.5 * 32767)
        y = int(0.5 * 32767)
        touch.write([0, 1, x & 0xFF, (x >> 8) & 0xFF, y & 0xFF, (y >> 8) & 0xFF])
        time.sleep(0.1)
        touch.write([0, 0, 0, 0, 0, 0])
        print("sent touch click at center")

    mouse = devices.get("mouse")
    if mouse:
        mouse.write([0, 0, 10, 10, 0])
        time.sleep(0.05)
        mouse.write([0, 0, 0, 0, 0])
        print("sent relative mouse movement")

    for dev in devices.values():
        dev.close()


if __name__ == "__main__":
    main()
