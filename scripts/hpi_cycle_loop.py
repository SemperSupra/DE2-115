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

PORTS = {
    "data": HPI_DATA,
    "mailbox": HPI_MAILBOX,
    "address": HPI_ADDRESS,
    "status": HPI_STATUS,
}


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


def write16(wb, addr, value):
    wb.write(addr, value & 0xFFFF)


def read16(wb, addr):
    return wb.read(addr) & 0xFFFF


def bridge_snapshot(wb):
    return {
        "cfg": wb.read(BRIDGE_CFG0),
        "ctrl": wb.read(BRIDGE_LAST_CTRL),
        "sample": wb.read(BRIDGE_LAST_SAMPLE) & 0xFFFF,
        "cy": wb.read(BRIDGE_LAST_CY) & 0xFFFF,
    }


def print_snapshot(prefix, snap):
    print(
        f"{prefix} cfg=0x{snap['cfg']:08x} ctrl=0x{snap['ctrl']:08x} "
        f"sample=0x{snap['sample']:04x} cy=0x{snap['cy']:04x}"
    )


def reset_cy(wb, args):
    cfg_rst = hpi_cfg(1, 0, 63, args.sample_offset, args.turnaround_cycles)
    cfg_run = hpi_cfg(1, 1, args.access_cycles, args.sample_offset, args.turnaround_cycles)
    wb.write(BRIDGE_CFG0, cfg_rst)
    time.sleep(args.reset_low)
    wb.write(BRIDGE_CFG0, cfg_run)
    time.sleep(args.reset_high)
    return cfg_run


def run_loop(args):
    wb = RemoteClient(host=args.host, port=args.port, csr_csv=args.csr_csv)
    wb.open()
    try:
        cfg_run = reset_cy(wb, args) if args.reset else hpi_cfg(
            1, args.rst_n, args.access_cycles, args.sample_offset, args.turnaround_cycles
        )
        wb.write(BRIDGE_CFG0, cfg_run)
        print(
            f"HPI_LOOP_CFG 0x{cfg_run:08x} mode={args.mode} port={args.port_name} "
            f"addr=0x{args.test_addr:04x} value=0x{args.test_data:04x} "
            f"period_ms={args.period_ms}"
        )
        print_snapshot("HPI_LOOP_INITIAL", bridge_snapshot(wb))

        hpi_port_addr = PORTS[args.port_name]
        count = 0
        while args.count == 0 or count < args.count:
            if args.mode == "read":
                if args.port_name == "data":
                    write16(wb, HPI_ADDRESS, args.test_addr)
                value = read16(wb, hpi_port_addr)
                snap = bridge_snapshot(wb)
                print(
                    f"HPI_LOOP_READ index={count} port={args.port_name} "
                    f"value=0x{value:04x} sample=0x{snap['sample']:04x} "
                    f"cy=0x{snap['cy']:04x} ctrl=0x{snap['ctrl']:08x}"
                )
            elif args.mode == "write":
                if args.port_name == "data":
                    write16(wb, HPI_ADDRESS, args.test_addr)
                value = (args.test_data + count * args.increment) & 0xFFFF
                write16(wb, hpi_port_addr, value)
                snap = bridge_snapshot(wb)
                print(
                    f"HPI_LOOP_WRITE index={count} port={args.port_name} "
                    f"value=0x{value:04x} sample=0x{snap['sample']:04x} "
                    f"cy=0x{snap['cy']:04x} ctrl=0x{snap['ctrl']:08x}"
                )
            else:
                write16(wb, HPI_ADDRESS, args.test_addr)
                write16(wb, HPI_DATA, (args.test_data + count * args.increment) & 0xFFFF)
                write16(wb, HPI_ADDRESS, args.test_addr)
                value = read16(wb, HPI_DATA)
                snap = bridge_snapshot(wb)
                print(
                    f"HPI_LOOP_RW index={count} addr=0x{args.test_addr:04x} "
                    f"read=0x{value:04x} sample=0x{snap['sample']:04x} "
                    f"cy=0x{snap['cy']:04x} ctrl=0x{snap['ctrl']:08x}"
                )
            sys.stdout.flush()
            count += 1
            if args.period_ms > 0:
                time.sleep(args.period_ms / 1000.0)
    finally:
        wb.close()


def main():
    p = argparse.ArgumentParser(description="Repeat CY7C67200 HPI cycles for external capture")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=1235)
    p.add_argument("--csr-csv", default="build/terasic_de2_115/csr.csv")
    p.add_argument("--start-server", action="store_true")
    p.add_argument("--board-ip", default="192.168.178.50")
    p.add_argument("--board-udp-port", type=int, default=1234)
    p.add_argument("--server-start-timeout", type=float, default=8.0)
    p.add_argument("--mode", choices=["read", "write", "rw"], default="rw")
    p.add_argument("--port-name", choices=sorted(PORTS), default="data")
    p.add_argument("--test-addr", type=lambda v: int(v, 0), default=0x1000)
    p.add_argument("--test-data", type=lambda v: int(v, 0), default=0x1234)
    p.add_argument("--increment", type=lambda v: int(v, 0), default=0)
    p.add_argument("--count", type=int, default=10, help="0 means run until interrupted")
    p.add_argument("--period-ms", type=float, default=100.0)
    p.add_argument("--access-cycles", type=int, default=63)
    p.add_argument("--sample-offset", type=int, default=8)
    p.add_argument("--turnaround-cycles", type=int, default=8)
    p.add_argument("--rst-n", type=lambda v: int(v, 0), choices=[0, 1], default=1,
                   help="CY HPI reset level while running cycles when --reset is not used")
    p.add_argument("--reset", action="store_true")
    p.add_argument("--reset-low", type=float, default=0.5)
    p.add_argument("--reset-high", type=float, default=0.5)
    args = p.parse_args()

    if not args.start_server:
        run_loop(args)
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
        run_loop(args)
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
