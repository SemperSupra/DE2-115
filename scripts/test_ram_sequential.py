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

def test_sequential(wb):
    HPI_DATA = USB_BASE + 0x8
    HPI_ADDRESS = USB_BASE + 0xC
    
    print("\n--- Testing RAM Sequential Read/Write ---")
    payload = [0x1111, 0x2222, 0x3333, 0x4444, 0x5555, 0x6666, 0x7777, 0x8888]
    
    # 1. Set Address once
    wb.write(HPI_ADDRESS, 0x1000)
    
    # 2. Write payload sequentially (auto-increment should handle the rest)
    print("Writing sequential payload...")
    for val in payload:
        wb.write(HPI_DATA, val)
        
    # 3. Reset Address
    wb.write(HPI_ADDRESS, 0x1000)
    
    # 4. Read payload back sequentially
    print("Reading back...")
    success = True
    
    # Dummy read required after address change? Let's do one dummy read.
    _ = wb.read(HPI_DATA)
    
    # Now read actuals. Note: Since we did a dummy read, does auto-increment happen?
    # Yes, reading HPI_DATA increments the address.
    # So if we do a dummy read, we just advanced to 0x1002!
    # Let's reset address again to read 0x1000!
    
    wb.write(HPI_ADDRESS, 0x1000)
    
    # Read without dummy, or account for pipeline delay.
    # The CY7C67200 datasheet says the first read after address write is valid?
    # Let's just read and see.
    reads = []
    for _ in payload:
        reads.append(wb.read(HPI_DATA) & 0xFFFF)
        
    for i, (expected, actual) in enumerate(zip(payload, reads)):
        addr = 0x1000 + (i * 2)
        match = "OK" if expected == actual else "FAIL"
        if expected != actual: success = False
        print(f"[{hex(addr)}] Expected: 0x{expected:04x} -> Read: 0x{actual:04x} ({match})")

def main():
    wb = RemoteClient()
    wb.open()
    try:
        timing = (6, 2, 2)
        wb.write(BRIDGE_CFG0, hpi_cfg(1, 0, timing[0], timing[1], timing[2]))
        time.sleep(0.5)
        wb.write(BRIDGE_CFG0, hpi_cfg(1, 1, timing[0], timing[1], timing[2]))
        time.sleep(0.5)
        
        test_sequential(wb)
    finally:
        wb.close()

if __name__ == "__main__":
    main()
