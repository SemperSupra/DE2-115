#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time

from litex import RemoteClient


USB_BASE = 0x82000000
HPI_DATA = USB_BASE + 0x000
HPI_MAILBOX = USB_BASE + 0x004
HPI_ADDRESS = USB_BASE + 0x008
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


def parse_list(text, cast):
    return [cast(item.strip()) for item in text.split(",") if item.strip()]


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


def read16(wb, addr):
    return wb.read(addr) & 0xFFFF


def write16(wb, addr, value):
    wb.write(addr, value & 0xFFFF)


def snapshot(wb):
    return (
        wb.read(BRIDGE_CFG0),
        wb.read(BRIDGE_LAST_CTRL),
        wb.read(BRIDGE_LAST_SAMPLE) & 0xFFFF,
        wb.read(BRIDGE_LAST_CY) & 0xFFFF,
    )


def run_sweep(args):
    reset_lows = parse_list(args.reset_lows, float)
    reset_highs = parse_list(args.reset_highs, float)
    samples = parse_list(args.sample_offsets, int)
    accesses = parse_list(args.access_cycles, int)

    wb = RemoteClient(host=args.host, port=args.port, csr_csv=args.csr_csv)
    wb.open()
    try:
        print(
            "HPI_RESET_SWEEP_BEGIN "
            f"addr=0x{args.test_addr:04x} data=0x{args.test_data:04x} "
            f"reset_lows={args.reset_lows} reset_highs={args.reset_highs} "
            f"access_cycles={args.access_cycles} sample_offsets={args.sample_offsets}"
        )
        for reset_low in reset_lows:
            for reset_high in reset_highs:
                for access in accesses:
                    for sample in samples:
                        cfg_rst = hpi_cfg(1, 0, 63, 8, args.turnaround_cycles)
                        cfg_run = hpi_cfg(1, 1, access, sample, args.turnaround_cycles)
                        wb.write(BRIDGE_CFG0, cfg_rst)
                        time.sleep(reset_low)
                        wb.write(BRIDGE_CFG0, cfg_run)
                        time.sleep(reset_high)

                        write16(wb, HPI_ADDRESS, args.test_addr)
                        data0 = read16(wb, HPI_DATA)
                        mailbox0 = read16(wb, HPI_MAILBOX)
                        status0 = read16(wb, HPI_STATUS)

                        write16(wb, HPI_ADDRESS, args.test_addr)
                        write16(wb, HPI_DATA, args.test_data)
                        write16(wb, HPI_ADDRESS, args.test_addr)
                        data1 = read16(wb, HPI_DATA)
                        mailbox1 = read16(wb, HPI_MAILBOX)
                        status1 = read16(wb, HPI_STATUS)
                        cfg, ctrl, sample_data, cy_data = snapshot(wb)

                        nonzero = data0 | mailbox0 | status0 | data1 | mailbox1 | status1
                        print(
                            "HPI_RESET_SWEEP "
                            f"reset_low={reset_low:.3f} reset_high={reset_high:.3f} "
                            f"access={access} sample={sample} cfg=0x{cfg:08x} "
                            f"data0=0x{data0:04x} mailbox0=0x{mailbox0:04x} status0=0x{status0:04x} "
                            f"data1=0x{data1:04x} mailbox1=0x{mailbox1:04x} status1=0x{status1:04x} "
                            f"last_sample=0x{sample_data:04x} last_cy=0x{cy_data:04x} "
                            f"ctrl=0x{ctrl:08x} nonzero=0x{nonzero:04x}"
                        )
                        sys.stdout.flush()
        print("HPI_RESET_SWEEP_END")
    finally:
        wb.close()


def main():
    p = argparse.ArgumentParser(description="Sweep CY7C67200 HPI reset release timing")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=1235)
    p.add_argument("--csr-csv", default="build/terasic_de2_115/csr.csv")
    p.add_argument("--start-server", action="store_true")
    p.add_argument("--board-ip", default="192.168.178.50")
    p.add_argument("--board-udp-port", type=int, default=1234)
    p.add_argument("--server-start-timeout", type=float, default=8.0)
    p.add_argument("--reset-lows", default="0.01,0.1,0.5,2.0")
    p.add_argument("--reset-highs", default="0.1,0.5,2.0,5.0")
    p.add_argument("--access-cycles", default="10,32,63")
    p.add_argument("--sample-offsets", default="2,8,16")
    p.add_argument("--turnaround-cycles", type=int, default=8)
    p.add_argument("--test-addr", type=lambda v: int(v, 0), default=0x1000)
    p.add_argument("--test-data", type=lambda v: int(v, 0), default=0x1234)
    args = p.parse_args()

    if not args.start_server:
        run_sweep(args)
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
        run_sweep(args)
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
