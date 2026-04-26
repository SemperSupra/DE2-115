#!/usr/bin/env python3
import argparse
import datetime as dt
import math
from pathlib import Path
import subprocess
import sys
import time

import cv2
from litex import RemoteClient


HEX_PATTERNS = [0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07]


def wait_for_server(host, port, timeout_s):
    deadline = time.time() + timeout_s
    last_error = None
    while time.time() < deadline:
        try:
            wb = RemoteClient(host=host, port=port)
            wb.open()
            wb.close()
            return
        except Exception as e:
            last_error = e
            time.sleep(0.25)
    raise RuntimeError(f"litex_server did not become ready: {last_error}")


def lcd_word(data=0, rs=0, rw=0, en=0, on=1, blon=1):
    return (
        ((on & 1) << 0)
        | ((blon & 1) << 1)
        | ((en & 1) << 2)
        | ((rw & 1) << 3)
        | ((rs & 1) << 4)
        | ((data & 0xFF) << 5)
    )


def lcd_pulse(lcd, data, rs):
    lcd.write(lcd_word(data, rs=rs, en=0))
    time.sleep(0.001)
    lcd.write(lcd_word(data, rs=rs, en=1))
    time.sleep(0.001)
    lcd.write(lcd_word(data, rs=rs, en=0))
    time.sleep(0.002)


def lcd_cmd(lcd, value):
    lcd_pulse(lcd, value, 0)
    if value in (0x01, 0x02):
        time.sleep(0.005)


def lcd_data(lcd, value):
    lcd_pulse(lcd, value, 1)


def lcd_write_text(lcd, line1, line2):
    lcd.write(lcd_word())
    time.sleep(0.05)
    lcd_cmd(lcd, 0x38)  # 8-bit, 2 lines, 5x8 font.
    lcd_cmd(lcd, 0x0C)  # Display on, cursor off.
    lcd_cmd(lcd, 0x01)  # Clear.
    lcd_cmd(lcd, 0x06)  # Increment.
    lcd_cmd(lcd, 0x80)
    for ch in line1[:16].ljust(16):
        lcd_data(lcd, ord(ch))
    lcd_cmd(lcd, 0xC0)
    for ch in line2[:16].ljust(16):
        lcd_data(lcd, ord(ch))


def configure_visual_state(wb, state_index):
    switches = wb.regs.switches_in.read() if hasattr(wb.regs, "switches_in") else 0

    if hasattr(wb.regs, "leds_r_out"):
        red_patterns = [0x1FFFF, 0x15555, 0x0AAAA, switches & 0x1FFFF]
        wb.regs.leds_r_out.write(red_patterns[state_index % len(red_patterns)])

    if hasattr(wb.regs, "leds_g_out"):
        green_patterns = [0x1FF, 0x155, 0x0AA, switches & 0x1FF]
        wb.regs.leds_g_out.write(green_patterns[state_index % len(green_patterns)])

    for i, pattern in enumerate(HEX_PATTERNS):
        reg_name = f"hex{i}_out"
        if hasattr(wb.regs, reg_name):
            getattr(wb.regs, reg_name).write(pattern if state_index % 2 == 0 else 0x7F ^ pattern)

    if hasattr(wb.regs, "lcd_out"):
        lcd_write_text(wb.regs.lcd_out, "DE2-115 SELFTEST", f"SW={switches:05X}")

    return switches


def open_camera(index, width, height):
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise RuntimeError(f"could not open camera index {index}")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    for _ in range(20):
        cap.read()
    return cap


def capture_opencv(args, wb, shots_dir, videos_dir, stamp):
    cap = None
    video = None
    try:
        switches = configure_visual_state(wb, 0)
        time.sleep(args.hold)

        cap = open_camera(args.camera, args.width, args.height)
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("camera opened but did not return a frame")

        screenshot = shots_dir / f"board_visual_selftest_{stamp}.jpg"
        cv2.imwrite(str(screenshot), frame)
        print(f"SCREENSHOT {screenshot}")

        video_path = videos_dir / f"board_visual_selftest_{stamp}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video = cv2.VideoWriter(str(video_path), fourcc, args.fps, (frame.shape[1], frame.shape[0]))
        start = time.time()
        next_state = start
        state = 0
        while time.time() - start < args.duration:
            now = time.time()
            if now >= next_state:
                switches = configure_visual_state(wb, state)
                state += 1
                next_state = now + args.state_seconds
            ret, frame = cap.read()
            if ret:
                video.write(frame)
            time.sleep(max(0.0, (1.0 / args.fps) / 2.0))

        print(f"VIDEO {video_path}")
        print(f"SWITCHES_FINAL 0x{switches:08x}")
    finally:
        if video is not None:
            video.release()
        if cap is not None:
            cap.release()


def run_checked(cmd):
    print("RUN " + " ".join(str(part) for part in cmd))
    completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if completed.stdout:
        sys.stdout.write(completed.stdout)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed with exit code {completed.returncode}: {' '.join(cmd)}")


def capture_agentwebcam(args, wb, shots_dir, videos_dir, stamp):
    switches = configure_visual_state(wb, 0)
    time.sleep(args.hold)

    screenshot = shots_dir / f"board_visual_selftest_{stamp}.jpg"
    run_checked([
        "agentwebcam",
        "snap",
        "--camera", str(args.camera),
        "--output", str(screenshot),
    ])
    print(f"SCREENSHOT {screenshot}")

    video_path = videos_dir / f"board_visual_selftest_{stamp}.mp4"
    record_cmd = [
        "agentwebcam",
        "record",
        "--camera", str(args.camera),
        "--output", str(video_path),
        "--duration", str(math.ceil(args.duration)),
        "--width", str(args.width),
        "--height", str(args.height),
        "--fps", str(args.fps),
        "--no-audio",
        "--no-subtitles",
        "--no-overlay",
    ]
    print("RUN " + " ".join(str(part) for part in record_cmd))
    proc = subprocess.Popen(record_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    start = time.time()
    next_state = start
    state = 0
    try:
        while proc.poll() is None:
            now = time.time()
            if now >= next_state:
                switches = configure_visual_state(wb, state)
                state += 1
                next_state = now + args.state_seconds
            time.sleep(0.05)
    finally:
        out, _ = proc.communicate(timeout=5)
        if out:
            sys.stdout.write(out)
    if proc.returncode != 0:
        raise RuntimeError(f"agentwebcam record failed with exit code {proc.returncode}")

    print(f"VIDEO {video_path}")
    print(f"SWITCHES_FINAL 0x{switches:08x}")


def capture_visual(args):
    out_dir = Path(args.out_dir)
    shots_dir = out_dir / "screenshots"
    videos_dir = out_dir / "videos"
    shots_dir.mkdir(parents=True, exist_ok=True)
    videos_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    wb = RemoteClient(host=args.host, port=args.port, csr_csv=args.csr_csv)
    wb.open()
    try:
        if args.capture_backend == "agentwebcam":
            capture_agentwebcam(args, wb, shots_dir, videos_dir, stamp)
        else:
            capture_opencv(args, wb, shots_dir, videos_dir, stamp)
        print("VISUAL_BOARD_SELFTEST_CAPTURE_PASS")
    finally:
        wb.close()


def main():
    p = argparse.ArgumentParser(description="Capture board screenshot/video during host-driven visual self-test")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=1235)
    p.add_argument("--csr-csv", default="build/terasic_de2_115/csr.csv")
    p.add_argument("--start-server", action="store_true")
    p.add_argument("--board-ip", default="192.168.178.50")
    p.add_argument("--board-udp-port", type=int, default=1234)
    p.add_argument("--server-start-timeout", type=float, default=8.0)
    p.add_argument("--camera", type=int, default=0)
    p.add_argument("--capture-backend", choices=("agentwebcam", "opencv"), default="agentwebcam")
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--height", type=int, default=1080)
    p.add_argument("--duration", type=float, default=12.0)
    p.add_argument("--hold", type=float, default=1.0)
    p.add_argument("--state-seconds", type=float, default=2.0)
    p.add_argument("--fps", type=float, default=15.0)
    p.add_argument("--out-dir", default="local_artifacts")
    args = p.parse_args()

    if not args.start_server:
        capture_visual(args)
        return

    cmd = [
        "litex_server",
        "--udp",
        "--udp-ip", args.board_ip,
        "--udp-port", str(args.board_udp_port),
        "--bind-ip", args.host,
        "--bind-port", str(args.port),
    ]
    server = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        wait_for_server(args.host, args.port, args.server_start_timeout)
        capture_visual(args)
    finally:
        server.terminate()
        try:
            out, _ = server.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            server.kill()
            out, _ = server.communicate(timeout=3)
        if out:
            sys.stdout.write(out)


if __name__ == "__main__":
    main()
