#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time

from litex import RemoteClient


USB_BASE = 0x82000000
BRIDGE_CFG0 = USB_BASE + 0x100
BRIDGE_LAST_CTRL = USB_BASE + 0x104
BRIDGE_LAST_SAMPLE = USB_BASE + 0x108
BRIDGE_LAST_CY = USB_BASE + 0x10C

HPI_DATA = USB_BASE + 0x8
HPI_ADDRESS = USB_BASE + 0xC

LEGACY_WARNING = (
    "WARNING: hpi_single_cycle_debug.py uses the legacy swapped HPI map "
    "(DATA=0x8, ADDR=0xc). Use cy_hpi_ladder_probe.py for accepted "
    "canonical Rung 1 evidence."
)


def hpi_cfg(force_rst, rst_n, access, sample, turnaround):
    return (
        (force_rst & 1)
        | ((rst_n & 1) << 1)
        | ((access & 0x3F) << 2)
        | ((sample & 0x3F) << 8)
        | ((turnaround & 0x3F) << 14)
    )


def wait_for_server(port, timeout_s):
    deadline = time.time() + timeout_s
    last_error = None
    while time.time() < deadline:
        try:
            wb = RemoteClient(host="127.0.0.1", port=port)
            wb.open()
            wb.close()
            return
        except Exception as e:
            last_error = e
            time.sleep(0.25)
    raise RuntimeError(f"litex_server did not become ready: {last_error}")


def dump_bridge(wb, label):
    cfg = wb.read(BRIDGE_CFG0)
    ctrl = wb.read(BRIDGE_LAST_CTRL)
    sample = wb.read(BRIDGE_LAST_SAMPLE) & 0xFFFF
    cy = wb.read(BRIDGE_LAST_CY) & 0xFFFF
    print(
        f"{label} cfg=0x{cfg:08x} ctrl=0x{ctrl:08x} "
        f"sample=0x{sample:04x} cy=0x{cy:04x}"
    )


def run_probe(port):
    wb = RemoteClient(host="127.0.0.1", port=port)
    wb.open()
    try:
        wb.write(BRIDGE_CFG0, hpi_cfg(1, 0, 6, 2, 2))
        time.sleep(0.05)
        wb.write(BRIDGE_CFG0, hpi_cfg(1, 1, 6, 2, 2))
        time.sleep(0.2)
        dump_bridge(wb, "HPI_SINGLE_INIT")

        wb.write(HPI_ADDRESS, 0xC000)
        dump_bridge(wb, "HPI_SINGLE_AFTER_ADDR_C000")

        wb.write(HPI_DATA, 0x5555)
        dump_bridge(wb, "HPI_SINGLE_AFTER_DATA_5555")

        wb.write(HPI_ADDRESS, 0x0000)
        _ = wb.read(HPI_DATA)
        read0 = wb.read(HPI_DATA) & 0xFFFF
        dump_bridge(wb, "HPI_SINGLE_AFTER_READ_0000")
        print(f"HPI_SINGLE_READBACK_0000 0x{read0:04x}")
    finally:
        wb.close()


def main():
    print(LEGACY_WARNING)
    p = argparse.ArgumentParser(description="Capture bridge debug CSRs around one HPI address/data transaction.")
    p.add_argument("--board-ip", default="192.168.178.50")
    p.add_argument("--board-udp-port", type=int, default=1234)
    p.add_argument("--bind-port", type=int, default=1234)
    p.add_argument("--start-server", action="store_true")
    args = p.parse_args()

    server = None
    if args.start_server:
        cmd = [
            "litex_server",
            "--udp",
            "--udp-ip",
            args.board_ip,
            "--udp-port",
            str(args.board_udp_port),
            "--bind-ip",
            "127.0.0.1",
            "--bind-port",
            str(args.bind_port),
        ]
        server = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    try:
        if server:
            wait_for_server(args.bind_port, 8.0)
        run_probe(args.bind_port)
    finally:
        if server:
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
