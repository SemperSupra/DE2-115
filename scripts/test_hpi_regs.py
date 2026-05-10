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

def test_reg(wb, addr, name):
    print(f"\n--- Testing {name} (0x{addr:02x}) ---")
    
    for val in [0x1000, 0x2000, 0x3000, 0x4000]:
        wb.write(USB_BASE + addr, val)
        # Double read
        r1 = wb.read(USB_BASE + addr) & 0xFFFF
        r2 = wb.read(USB_BASE + addr) & 0xFFFF
        print(f"Wrote 0x{val:04x} -> Read1=0x{r1:04x}, Read2=0x{r2:04x}")

def main():
    wb = RemoteClient()
    wb.open()
    try:
        timing = (6, 2, 2)
        wb.write(BRIDGE_CFG0, hpi_cfg(1, 0, timing[0], timing[1], timing[2]))
        time.sleep(0.5)
        wb.write(BRIDGE_CFG0, hpi_cfg(1, 1, timing[0], timing[1], timing[2]))
        time.sleep(1.0)
        
        test_reg(wb, 0x0, "Port 0")
        test_reg(wb, 0x4, "Port 4")
        test_reg(wb, 0x8, "Port 8")
        test_reg(wb, 0xC, "Port C")
        
    finally:
        wb.close()

if __name__ == "__main__":
    main()
