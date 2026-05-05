#!/usr/bin/env python3
import argparse
import itertools
import subprocess
import sys
import time

from litex import RemoteClient


USB_BASE = 0x82000000
BRIDGE_CFG0 = USB_BASE + 0x100
BRIDGE_LAST_CTRL = USB_BASE + 0x104
BRIDGE_LAST_SAMPLE = USB_BASE + 0x108
BRIDGE_LAST_CY = USB_BASE + 0x10C

PHYS_PORTS = [USB_BASE + 0x000, USB_BASE + 0x004, USB_BASE + 0x008, USB_BASE + 0x00C]
LOGICAL_NAMES = ("data", "mailbox", "address", "status")


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


def snapshot(wb):
    return {
        "ctrl": wb.read(BRIDGE_LAST_CTRL),
        "sample": wb.read(BRIDGE_LAST_SAMPLE) & 0xFFFF,
        "cy": wb.read(BRIDGE_LAST_CY) & 0xFFFF,
    }


def reset_cy(wb, args):
    cfg_rst = hpi_cfg(1, 0, 63, args.sample_offset, args.turnaround_cycles)
    cfg_run = hpi_cfg(1, 1, args.access_cycles, args.sample_offset, args.turnaround_cycles)
    wb.write(BRIDGE_CFG0, cfg_rst)
    time.sleep(args.reset_low)
    wb.write(BRIDGE_CFG0, cfg_run)
    time.sleep(args.reset_high)
    return cfg_run


def fmt_map(mapping):
    return ",".join(f"{name}=A{mapping[name]}" for name in LOGICAL_NAMES)


def run_probe(args):
    wb = RemoteClient(host=args.host, port=args.port, csr_csv=args.csr_csv)
    wb.open()
    try:
        cfg_run = reset_cy(wb, args)
        print(
            f"HPI_ADDR_PERM_BEGIN cfg=0x{cfg_run:08x} "
            f"addr=0x{args.test_addr:04x} data=0x{args.test_data:04x} "
            f"mailbox=0x{args.mailbox_value:04x} settle={args.settle}s"
        )

        any_nonzero = 0
        any_match = 0
        for index, perm in enumerate(itertools.permutations(range(4))):
            mapping = dict(zip(LOGICAL_NAMES, perm))
            port = {name: PHYS_PORTS[mapping[name]] for name in LOGICAL_NAMES}
            if args.reset_each:
                reset_cy(wb, args)

            baseline = {
                "data": read16(wb, port["data"]),
                "mailbox": read16(wb, port["mailbox"]),
                "status": read16(wb, port["status"]),
            }

            write16(wb, port["mailbox"], args.mailbox_value)
            mailbox_write = snapshot(wb)
            time.sleep(args.settle)
            after_mailbox = {
                "mailbox": read16(wb, port["mailbox"]),
                "status": read16(wb, port["status"]),
            }

            write16(wb, port["address"], args.test_addr)
            write16(wb, port["data"], args.test_data)
            data_write = snapshot(wb)
            write16(wb, port["address"], args.test_addr)
            readback = read16(wb, port["data"])
            data_read = snapshot(wb)

            values = [
                baseline["data"],
                baseline["mailbox"],
                baseline["status"],
                after_mailbox["mailbox"],
                after_mailbox["status"],
                readback,
                data_read["sample"],
                data_read["cy"],
            ]
            nonzero = any(v != 0 for v in values)
            match = readback == (args.test_data & 0xFFFF)
            any_nonzero |= int(nonzero)
            any_match |= int(match)

            print(
                "HPI_ADDR_PERM_RESULT "
                f"index={index:02d} map={fmt_map(mapping)} "
                f"base_data=0x{baseline['data']:04x} base_mailbox=0x{baseline['mailbox']:04x} "
                f"base_status=0x{baseline['status']:04x} "
                f"post_mailbox=0x{after_mailbox['mailbox']:04x} post_status=0x{after_mailbox['status']:04x} "
                f"mailbox_write_sample=0x{mailbox_write['sample']:04x} mailbox_write_cy=0x{mailbox_write['cy']:04x} "
                f"data_write_sample=0x{data_write['sample']:04x} data_write_cy=0x{data_write['cy']:04x} "
                f"readback=0x{readback:04x} read_sample=0x{data_read['sample']:04x} "
                f"read_cy=0x{data_read['cy']:04x} read_ctrl=0x{data_read['ctrl']:08x} "
                f"nonzero={int(nonzero)} match={int(match)}"
            )
            sys.stdout.flush()

        print(f"HPI_ADDR_PERM_SUMMARY nonzero={any_nonzero} match={any_match}")
        print("HPI_ADDR_PERM_END")
    finally:
        wb.close()


def main():
    p = argparse.ArgumentParser(description="Try all HPI logical-port mappings across the four address slots")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=1235)
    p.add_argument("--csr-csv", default="build/terasic_de2_115/csr.csv")
    p.add_argument("--start-server", action="store_true")
    p.add_argument("--board-ip", default="192.168.178.50")
    p.add_argument("--board-udp-port", type=int, default=1234)
    p.add_argument("--server-start-timeout", type=float, default=8.0)
    p.add_argument("--test-addr", type=lambda v: int(v, 0), default=0x1000)
    p.add_argument("--test-data", type=lambda v: int(v, 0), default=0x1234)
    p.add_argument("--mailbox-value", type=lambda v: int(v, 0), default=0xFA50)
    p.add_argument("--settle", type=float, default=0.05)
    p.add_argument("--access-cycles", type=int, default=63)
    p.add_argument("--sample-offset", type=int, default=8)
    p.add_argument("--turnaround-cycles", type=int, default=8)
    p.add_argument("--reset-low", type=float, default=0.5)
    p.add_argument("--reset-high", type=float, default=0.5)
    p.add_argument("--reset-each", action="store_true")
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
