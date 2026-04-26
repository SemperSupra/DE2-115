#!/usr/bin/env python3
import argparse
import sys
import time

import serial


def main():
    p = argparse.ArgumentParser(description="Bounded UART capture helper")
    p.add_argument("--port", default="COM3")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--duration", type=float, default=10.0)
    p.add_argument("--outfile")
    args = p.parse_args()

    deadline = time.time() + args.duration
    lines = []
    with serial.Serial(args.port, args.baud, timeout=0.2) as ser:
        while time.time() < deadline:
            raw = ser.readline()
            if not raw:
                continue
            line = raw.decode("ascii", errors="replace").rstrip()
            stamp = time.strftime("%H:%M:%S")
            formatted = f"[{stamp}] {line}"
            print(formatted)
            lines.append(formatted)

    if args.outfile:
        with open(args.outfile, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
