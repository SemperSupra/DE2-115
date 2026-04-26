#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time

from litex import RemoteClient


HEX_PATTERNS = [0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07]


def require_reg(wb, name):
    if not hasattr(wb.regs, name):
        raise RuntimeError(f"CSR register missing: {name}")
    return getattr(wb.regs, name)


def write_read_check(reg, value, mask, label):
    reg.write(value)
    got = reg.read() & mask
    exp = value & mask
    if got != exp:
        raise RuntimeError(f"{label} mismatch got=0x{got:x} expected=0x{exp:x}")
    return got


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


def run_smoke(args):
    wb = RemoteClient(host=args.host, port=args.port, csr_csv=args.csr_csv)
    wb.open()
    try:
        ident = "".join(chr(wb.read(0xF0006000 + 4 * i) & 0xFF) for i in range(24))
        print(f"IDENT_PREFIX {ident!r}")

        switches = require_reg(wb, "switches_in").read()
        print(f"SWITCHES 0x{switches:08x}")

        leds_r = require_reg(wb, "leds_r_out")
        before_r = leds_r.read()
        for value in (0x00000, 0x15555, 0x0AAAA, 0x1FFFF):
            write_read_check(leds_r, value, 0x1FFFF, "leds_r")
        leds_r.write(before_r)
        print("LEDS_R_RW_OK")

        if hasattr(wb.regs, "leds_g_out"):
            # Firmware owns green LEDs as heartbeat; probe access but do not use
            # as a sustained correctness oracle.
            wb.regs.leds_g_out.write(0x5A)
            print(f"LEDS_G_PROBE 0x{wb.regs.leds_g_out.read():08x}")

        for index, pattern in enumerate(HEX_PATTERNS):
            reg = require_reg(wb, f"hex{index}_out")
            write_read_check(reg, pattern, 0x7F, f"hex{index}")
        print("SEVEN_SEG_RW_OK")

        if hasattr(wb.regs, "lcd_out"):
            lcd = wb.regs.lcd_out
            before_lcd = lcd.read()
            for value in (0x000, 0x155, 0x2AA):
                write_read_check(lcd, value, 0x7FF, "lcd")
            lcd.write(before_lcd)
            print("LCD_GPIO_RW_OK")

        print("BOARD_GPIO_SMOKE_TEST_PASS")
    finally:
        wb.close()


def main():
    p = argparse.ArgumentParser(description="DE2-115 GPIO-style device smoke test over Etherbone")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=1235)
    p.add_argument("--csr-csv", default="build/terasic_de2_115/csr.csv")
    p.add_argument("--start-server", action="store_true")
    p.add_argument("--board-ip", default="192.168.178.50")
    p.add_argument("--board-udp-port", type=int, default=1234)
    p.add_argument("--server-start-timeout", type=float, default=8.0)
    args = p.parse_args()

    if not args.start_server:
        run_smoke(args)
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
        run_smoke(args)
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
