#!/usr/bin/env python3
import argparse
from litex import RemoteClient


def main():
    p = argparse.ArgumentParser(description="Simple Etherbone CSR probe")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=1234)
    p.add_argument("--csr-csv", default="build/terasic_de2_115/csr.csv")
    p.add_argument("--addr", default="0xf0000004", help="CSR address (hex or int)")
    args = p.parse_args()

    addr = int(args.addr, 0)
    wb = RemoteClient(host=args.host, port=args.port, csr_csv=args.csr_csv)
    wb.open()
    try:
        value = wb.read(addr)
        print(f"OPEN_OK addr=0x{addr:08x} value=0x{value:08x}")
    finally:
        wb.close()


if __name__ == "__main__":
    main()

