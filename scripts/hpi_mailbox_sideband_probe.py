#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time

from litex import RemoteClient


USB_BASE = 0x82000000
HPI_MAILBOX = USB_BASE + 0x004
HPI_STATUS = USB_BASE + 0x00C
BRIDGE_CFG0 = USB_BASE + 0x100
BRIDGE_LAST_CTRL = USB_BASE + 0x104
BRIDGE_LAST_SAMPLE = USB_BASE + 0x108
BRIDGE_LAST_CY = USB_BASE + 0x10C


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


def parse_values(text):
    return [int(item.strip(), 0) & 0xFFFF for item in text.split(",") if item.strip()]


def write16(wb, addr, value):
    wb.write(addr, value & 0xFFFF)


def read16(wb, addr):
    return wb.read(addr) & 0xFFFF


def snapshot(wb):
    return {
        "cfg": wb.read(BRIDGE_CFG0),
        "ctrl": wb.read(BRIDGE_LAST_CTRL),
        "sample": wb.read(BRIDGE_LAST_SAMPLE) & 0xFFFF,
        "cy": wb.read(BRIDGE_LAST_CY) & 0xFFFF,
    }


def run_probe(args):
    values = parse_values(args.values)
    wb = RemoteClient(host=args.host, port=args.port, csr_csv=args.csr_csv)
    wb.open()
    try:
        if args.reset:
            cfg_rst = hpi_cfg(1, 0, 63, args.sample_offset, args.turnaround_cycles)
            cfg_run = hpi_cfg(1, 1, args.access_cycles, args.sample_offset, args.turnaround_cycles)
            wb.write(BRIDGE_CFG0, cfg_rst)
            time.sleep(args.reset_low)
            wb.write(BRIDGE_CFG0, cfg_run)
            time.sleep(args.reset_high)
        else:
            cfg_run = hpi_cfg(1, 1, args.access_cycles, args.sample_offset, args.turnaround_cycles)
            wb.write(BRIDGE_CFG0, cfg_run)

        if args.pre_write_delay > 0:
            time.sleep(args.pre_write_delay)

        print(
            f"HPI_MAILBOX_SIDEBAND_BEGIN cfg=0x{cfg_run:08x} "
            f"values={','.join(f'0x{v:04x}' for v in values)} settle={args.settle}s"
        )
        for index, value in enumerate(values):
            write16(wb, HPI_MAILBOX, value)
            write_snap = snapshot(wb)
            time.sleep(args.settle)
            status = read16(wb, HPI_STATUS)
            mailbox = read16(wb, HPI_MAILBOX)
            read_snap = snapshot(wb)
            print(
                "HPI_MAILBOX_SIDEBAND "
                f"index={index} wrote=0x{value:04x} status=0x{status:04x} "
                f"mailbox=0x{mailbox:04x} "
                f"write_ctrl=0x{write_snap['ctrl']:08x} write_sample=0x{write_snap['sample']:04x} "
                f"write_cy=0x{write_snap['cy']:04x} read_ctrl=0x{read_snap['ctrl']:08x} "
                f"read_sample=0x{read_snap['sample']:04x} read_cy=0x{read_snap['cy']:04x}"
            )
            sys.stdout.flush()
        print("HPI_MAILBOX_SIDEBAND_END")
    finally:
        wb.close()


def main():
    p = argparse.ArgumentParser(description="Write HPI mailbox values and read status/mailbox after a settle interval")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=1235)
    p.add_argument("--csr-csv", default="build/terasic_de2_115/csr.csv")
    p.add_argument("--start-server", action="store_true")
    p.add_argument("--board-ip", default="192.168.178.50")
    p.add_argument("--board-udp-port", type=int, default=1234)
    p.add_argument("--server-start-timeout", type=float, default=8.0)
    p.add_argument("--values", default="0xfa50,0xce00,0x0000,0xffff")
    p.add_argument("--settle", type=float, default=0.25)
    p.add_argument("--access-cycles", type=int, default=63)
    p.add_argument("--sample-offset", type=int, default=8)
    p.add_argument("--turnaround-cycles", type=int, default=8)
    p.add_argument("--reset", action="store_true")
    p.add_argument("--reset-low", type=float, default=0.5)
    p.add_argument("--reset-high", type=float, default=0.5)
    p.add_argument("--pre-write-delay", type=float, default=0.0)
    args = p.parse_args()

    if not args.start_server:
        run_probe(args)
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
        run_probe(args)
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
