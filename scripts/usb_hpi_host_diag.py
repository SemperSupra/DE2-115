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


def dump_bridge(wb, prefix):
    cfg = wb.read(BRIDGE_CFG0)
    ctrl = wb.read(BRIDGE_LAST_CTRL)
    sample = wb.read(BRIDGE_LAST_SAMPLE) & 0xFFFF
    cy = wb.read(BRIDGE_LAST_CY) & 0xFFFF
    print(f"{prefix} cfg=0x{cfg:08x} ctrl=0x{ctrl:08x} sample=0x{sample:04x} cy=0x{cy:04x}")


def run_diag(args):
    if args.initial_delay:
        time.sleep(args.initial_delay)
    wb = RemoteClient(host=args.host, port=args.port, csr_csv=args.csr_csv)
    wb.open()
    try:
        # Phase 1: Robust Reset & Timing Optimization
        print(f"Applying Reset (Low={args.reset_low}s, High={args.reset_high}s)...")
        # Hold in reset, slow timing for safety during reset state
        cfg_rst = hpi_cfg(1, 0, 63, 8, 8)
        wb.write(BRIDGE_CFG0, cfg_rst)
        time.sleep(args.reset_low)
        # Release reset, apply optimized timing
        cfg_run = hpi_cfg(1, 1, args.access_cycles, args.sample_offset, args.turnaround_cycles)
        wb.write(BRIDGE_CFG0, cfg_run)
        time.sleep(args.reset_high)

        print(f"HPI_HOST_CFG 0x{cfg_run:08x}")
        dump_bridge(wb, "HPI_HOST_INITIAL")

        # Phase 2: Hardware Register Loopback (HPI_ADDRESS is a latch)
        test_val = 0xABCD
        print(f"Testing HPI_ADDRESS latch with 0x{test_val:04x}...")
        write16(wb, HPI_ADDRESS, test_val)
        read_val = read16(wb, HPI_ADDRESS)
        print(f"HPI_ADDRESS Result: Wrote=0x{test_val:04x}, Read=0x{read_val:04x}")

        if read_val == test_val:
            print("HPI_HARDWARE_INTERFACE_OK")
        else:
            print("HPI_HARDWARE_INTERFACE_FAIL")

        # Phase 3: Memory R/W Test
        print(f"Testing Memory R/W at 0x{args.test_addr:04x} with 0x{args.test_data:04x}...")
        write16(wb, HPI_ADDRESS, args.test_addr)
        write16(wb, HPI_DATA, args.test_data)
        dump_bridge(wb, "HPI_HOST_AFTER_WRITE")

        write16(wb, HPI_ADDRESS, args.test_addr)
        readback = read16(wb, HPI_DATA)
        dump_bridge(wb, "HPI_HOST_AFTER_READ")

        status = read16(wb, HPI_STATUS)
        mailbox = read16(wb, HPI_MAILBOX)
        print(
            f"HPI_HOST_RESULT addr=0x{args.test_addr:04x} "
            f"wrote=0x{args.test_data:04x} read=0x{readback:04x} "
            f"status=0x{status:04x} mailbox=0x{mailbox:04x}"
        )
        
        if readback == (args.test_data & 0xFFFF):
            print("HPI_MEM_RW_PASS")
        else:
            print("HPI_MEM_RW_FAIL")
            if args.fail_on_mismatch:
                raise SystemExit(1)
                
    finally:
        wb.close()


def main():
    p = argparse.ArgumentParser(description="Host-triggered CY7C67200 HPI diagnostic")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=1235)
    p.add_argument("--csr-csv", default="build/terasic_de2_115/csr.csv")
    p.add_argument("--start-server", action="store_true")
    p.add_argument("--board-ip", default="192.168.178.50")
    p.add_argument("--board-udp-port", type=int, default=1234)
    p.add_argument("--server-start-timeout", type=float, default=8.0)
    p.add_argument("--test-addr", type=lambda v: int(v, 0), default=0x1000)
    p.add_argument("--test-data", type=lambda v: int(v, 0), default=0x1234)
    p.add_argument("--access-cycles", type=int, default=10) # 200ns @ 50MHz
    p.add_argument("--sample-offset", type=int, default=2)
    p.add_argument("--turnaround-cycles", type=int, default=2)
    p.add_argument("--reset-low", type=float, default=0.5)
    p.add_argument("--reset-high", type=float, default=0.5)
    p.add_argument("--initial-delay", type=float, default=0.0)
    p.add_argument("--fail-on-mismatch", action="store_true")
    args = p.parse_args()

    if not args.start_server:
        run_diag(args)
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
        run_diag(args)
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
