#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time

from litex import RemoteClient


USB_BASE = 0x82000000
BRIDGE_CFG0 = USB_BASE + 0x100


def hpi_cfg(force_rst, rst_n, access, sample, turnaround):
    return (
        (force_rst & 1)
        | ((rst_n & 1) << 1)
        | ((access & 0x3F) << 2)
        | ((sample & 0x3F) << 8)
        | ((turnaround & 0x3F) << 14)
    )


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


def write_reset(args):
    wb = RemoteClient(host=args.host, port=args.port, csr_csv=args.csr_csv)
    wb.open()
    try:
        cfg = hpi_cfg(
            1,
            1 if args.rst_n else 0,
            args.access_cycles,
            args.sample_offset,
            args.turnaround_cycles,
        )
        wb.write(BRIDGE_CFG0, cfg)
        print(f"HPI_SET_RESET rst_n={1 if args.rst_n else 0} cfg=0x{cfg:08x}")
    finally:
        wb.close()


def main():
    p = argparse.ArgumentParser(description="Set CY7C67200 HPI reset bridge state")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=1235)
    p.add_argument("--csr-csv", default="build/terasic_de2_115/csr.csv")
    p.add_argument("--start-server", action="store_true")
    p.add_argument("--board-ip", default="192.168.178.50")
    p.add_argument("--board-udp-port", type=int, default=1234)
    p.add_argument("--server-start-timeout", type=float, default=8.0)
    p.add_argument("--rst-n", type=lambda v: int(v, 0), choices=[0, 1], required=True)
    p.add_argument("--access-cycles", type=int, default=63)
    p.add_argument("--sample-offset", type=int, default=8)
    p.add_argument("--turnaround-cycles", type=int, default=8)
    args = p.parse_args()

    if not args.start_server:
        write_reset(args)
        return

    cmd = [
        "litex_server",
        "--udp",
        "--udp-ip",
        args.board_ip,
        "--udp-port",
        str(args.board_udp_port),
        "--bind-ip",
        args.host,
        "--bind-port",
        str(args.port),
    ]
    server = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        wait_for_server(args.host, args.port, args.server_start_timeout)
        write_reset(args)
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
