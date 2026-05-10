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

def test_reads(wb, timing):
    wb.write(BRIDGE_CFG0, hpi_cfg(1, 0, timing[0], timing[1], timing[2]))
    time.sleep(0.5)
    wb.write(BRIDGE_CFG0, hpi_cfg(1, 1, timing[0], timing[1], timing[2]))
    time.sleep(1.0)
    
    print("\n--- Consecutive Reads ---")
    ports = [0x0, 0x4, 0x8, 0xC]
    
    for port in ports:
        addr = USB_BASE + port
        reads = []
        for _ in range(10):
            reads.append(wb.read(addr) & 0xFFFF)
        
        # Format the output nicely
        read_strs = [f"0x{r:04x}" for r in reads]
        print(f"Port 0x{port:02x}: {', '.join(read_strs)}")

def main():
    wb = RemoteClient()
    wb.open()
    try:
        timing = (6, 2, 2)
        test_reads(wb, timing)
    finally:
        wb.close()

if __name__ == "__main__":
    main()
