import time
from litex import RemoteClient

USB_BASE = 0x82000000
BRIDGE_CFG0 = USB_BASE + 0x100
HPI_ADDRESS = USB_BASE + 0xC
HPI_DATA = USB_BASE + 0x8

def hpi_cfg(force_rst, rst_n, access, sample, turnaround):
    return (
        (force_rst & 1)
        | ((rst_n & 1) << 1)
        | ((access & 0x3F) << 2)
        | ((sample & 0x3F) << 8)
        | ((turnaround & 0x3F) << 14)
    )

def test_alias(wb):
    wb.write(BRIDGE_CFG0, hpi_cfg(1, 0, 6, 2, 2))
    time.sleep(0.1)
    wb.write(BRIDGE_CFG0, hpi_cfg(1, 1, 6, 2, 2))
    time.sleep(0.5)
    
    # Write to 0x0000
    wb.write(HPI_ADDRESS, 0x0000)
    wb.write(HPI_DATA, 0x0000) # Clear
    
    addresses_to_test = [0x1000, 0x2000, 0x4000, 0x8000, 0xC000]
    
    for i, addr in enumerate(addresses_to_test):
        val = 0x1111 * (i + 1)
        wb.write(HPI_ADDRESS, addr)
        wb.write(HPI_DATA, val)
        
        # Read from 0x0000 to see if it aliased
        wb.write(HPI_ADDRESS, 0x0000)
        _ = wb.read(HPI_DATA)
        r0 = wb.read(HPI_DATA) & 0xFFFF
        
        # Read from the actual address
        wb.write(HPI_ADDRESS, addr)
        _ = wb.read(HPI_DATA)
        ra = wb.read(HPI_DATA) & 0xFFFF
        
        print(f"Wrote 0x{val:04x} to 0x{addr:04x}. Read 0x0000: 0x{r0:04x}, Read 0x{addr:04x}: 0x{ra:04x}")

def main():
    wb = RemoteClient()
    wb.open()
    try:
        test_alias(wb)
    finally:
        wb.close()

if __name__ == "__main__":
    main()
