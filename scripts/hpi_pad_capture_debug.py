#!/usr/bin/env python3
import argparse
import subprocess
import time

from litex import RemoteClient


USB_BASE = 0x82000000
BRIDGE_CFG0 = USB_BASE + 0x100
HPI_DATA = USB_BASE + 0x8
HPI_ADDRESS = USB_BASE + 0xC

CAP_ADDR_WRITE_LO = USB_BASE + 0x110
CAP_ADDR_WRITE_HI = USB_BASE + 0x114
CAP_DATA_WRITE_LO = USB_BASE + 0x118
CAP_DATA_WRITE_HI = USB_BASE + 0x11C
CAP_DATA_READ_LO = USB_BASE + 0x120
CAP_DATA_READ_HI = USB_BASE + 0x124


def hpi_cfg(force_rst, rst_n, access, sample, turnaround):
    return (
        (force_rst & 1)
        | ((rst_n & 1) << 1)
        | ((access & 0x3F) << 2)
        | ((sample & 0x3F) << 8)
        | ((turnaround & 0x3F) << 14)
    )


def read64(wb, lo_addr, hi_addr):
    lo = wb.read(lo_addr) & 0xFFFFFFFF
    hi = wb.read(hi_addr) & 0xFFFFFFFF
    return lo | (hi << 32)


def bits(value, start, width):
    return (value >> start) & ((1 << width) - 1)


def decode_capture(name, value):
    fields = {
        "captured": bits(value, 63, 1),
        "latched_we": bits(value, 62, 1),
        "wb_we": bits(value, 61, 1),
        "hpi_access": bits(value, 60, 1),
        "hpi_rst_n": bits(value, 59, 1),
        "hpi_cs_n": bits(value, 58, 1),
        "hpi_rd_n": bits(value, 57, 1),
        "hpi_wr_n": bits(value, 56, 1),
        "hpi_addr": bits(value, 54, 2),
        "state": bits(value, 52, 2),
        "count": bits(value, 46, 6),
        "local_adr": bits(value, 32, 14),
        "wb_dat_w": bits(value, 16, 16),
        "hpi_data": bits(value, 0, 16),
    }
    print(
        f"{name}: raw=0x{value:016x} captured={fields['captured']} "
        f"we={fields['latched_we']} addr={fields['hpi_addr']} "
        f"cs_n={fields['hpi_cs_n']} rd_n={fields['hpi_rd_n']} wr_n={fields['hpi_wr_n']} "
        f"count={fields['count']} local=0x{fields['local_adr']:04x} "
        f"wb=0x{fields['wb_dat_w']:04x} hpi_data=0x{fields['hpi_data']:04x}"
    )


def wait_for_server(port, timeout):
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            wb = RemoteClient(host="127.0.0.1", port=port)
            wb.open()
            wb.close()
            return
        except Exception as exc:
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"litex_server did not become ready: {last_error}")


def run_probe(wb, address, value):
    wb.write(BRIDGE_CFG0, hpi_cfg(1, 0, 6, 2, 2))
    time.sleep(0.1)
    wb.write(BRIDGE_CFG0, hpi_cfg(1, 1, 6, 2, 2))
    time.sleep(0.5)

    wb.write(HPI_ADDRESS, address)
    wb.write(HPI_DATA, value)
    wb.write(HPI_ADDRESS, 0x0000)
    _ = wb.read(HPI_DATA)
    readback = wb.read(HPI_DATA) & 0xFFFF

    print(f"HPI_PAD_CAPTURE target=0x{address:04x} write=0x{value:04x} read0=0x{readback:04x}")
    decode_capture("ADDR_WRITE", read64(wb, CAP_ADDR_WRITE_LO, CAP_ADDR_WRITE_HI))
    decode_capture("DATA_WRITE", read64(wb, CAP_DATA_WRITE_LO, CAP_DATA_WRITE_HI))
    decode_capture("DATA_READ", read64(wb, CAP_DATA_READ_LO, CAP_DATA_READ_HI))


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Exercise one HPI alias write/read and decode pad snapshots. "
            "Requires the experimental pad-capture RTL; the default bridge does not expose these registers."
        )
    )
    parser.add_argument("--board-ip", default="192.168.178.50")
    parser.add_argument("--board-udp-port", type=int, default=1234)
    parser.add_argument("--bind-port", type=int, default=1235)
    parser.add_argument("--start-server", action="store_true")
    parser.add_argument("--address", type=lambda x: int(x, 0), default=0xC000)
    parser.add_argument("--value", type=lambda x: int(x, 0), default=0x5555)
    parser.add_argument("--server-start-timeout", type=float, default=10.0)
    parser.add_argument("--experimental-rtl", action="store_true")
    args = parser.parse_args()

    if not args.experimental_rtl:
        parser.error("refusing to run: pass --experimental-rtl only when the pad-capture RTL is programmed")

    server = None
    if args.start_server:
        server = subprocess.Popen(
            [
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
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        wait_for_server(args.bind_port, args.server_start_timeout)

    wb = RemoteClient(host="127.0.0.1", port=args.bind_port)
    wb.open()
    try:
        run_probe(wb, args.address & 0xFFFF, args.value & 0xFFFF)
    finally:
        wb.close()
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


if __name__ == "__main__":
    main()
