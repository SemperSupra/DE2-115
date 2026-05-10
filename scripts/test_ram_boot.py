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

def test_mem(wb):
    # Test Hypothesis: 0x8 = Address, 0xC = Data
    HPI_ADDRESS = USB_BASE + 0x8
    HPI_DATA = USB_BASE + 0xC
    
    print("\n--- Testing RAM Read/Write (0x8=Addr, 0xC=Data) ---")
    
    wb.write(HPI_ADDRESS, 0x1000)
    wb.write(HPI_DATA, 0x55AA)
    wb.write(HPI_ADDRESS, 0x1002)
    wb.write(HPI_DATA, 0x33CC)
    
    wb.write(HPI_ADDRESS, 0x1000)
    _ = wb.read(HPI_DATA)
    r1 = wb.read(HPI_DATA) & 0xFFFF
    
    wb.write(HPI_ADDRESS, 0x1002)
    _ = wb.read(HPI_DATA)
    r2 = wb.read(HPI_DATA) & 0xFFFF
    
    print(f"Read 0x1000: 0x{r1:04x} (Expected 0x55AA)")
    print(f"Read 0x1002: 0x{r2:04x} (Expected 0x33CC)")
    
    # Test Hypothesis: 0xC = Address, 0x8 = Data
    print("\n--- Testing RAM Read/Write (0xC=Addr, 0x8=Data) ---")
    HPI_ADDRESS = USB_BASE + 0xC
    HPI_DATA = USB_BASE + 0x8
    
    wb.write(HPI_ADDRESS, 0x1004)
    wb.write(HPI_DATA, 0x1122)
    wb.write(HPI_ADDRESS, 0x1006)
    wb.write(HPI_DATA, 0x3344)
    
    wb.write(HPI_ADDRESS, 0x1004)
    _ = wb.read(HPI_DATA)
    r3 = wb.read(HPI_DATA) & 0xFFFF
    
    wb.write(HPI_ADDRESS, 0x1006)
    _ = wb.read(HPI_DATA)
    r4 = wb.read(HPI_DATA) & 0xFFFF
    
    print(f"Read 0x1004: 0x{r3:04x} (Expected 0x1122)")
    print(f"Read 0x1006: 0x{r4:04x} (Expected 0x3344)")

def main():
    wb = RemoteClient()
    wb.open()
    try:
        timing = (6, 2, 2)
        wb.write(BRIDGE_CFG0, hpi_cfg(1, 0, timing[0], timing[1], timing[2]))
        time.sleep(1.0)
        wb.write(BRIDGE_CFG0, hpi_cfg(1, 1, timing[0], timing[1], timing[2]))
        time.sleep(1.0)
        
        test_mem(wb)
    finally:
        wb.close()

if __name__ == "__main__":
    main()
