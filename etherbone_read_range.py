import argparse
from litex import RemoteClient

def main():
    p = argparse.ArgumentParser(description="Read a range of memory via Etherbone")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=1234)
    p.add_argument("--csr-csv", default="build/terasic_de2_115/csr.csv")
    p.add_argument("--addr", default="0xf0005800")
    p.add_argument("--count", type=int, default=16)
    args = p.parse_args()

    addr = int(args.addr, 0)
    wb = RemoteClient(host=args.host, port=args.port, csr_csv=args.csr_csv)
    wb.open()
    try:
        for i in range(args.count):
            cur_addr = addr + i * 4
            value = wb.read(cur_addr)
            print(f"0x{cur_addr:08x}: 0x{value:08x}")
    finally:
        wb.close()

if __name__ == "__main__":
    main()
