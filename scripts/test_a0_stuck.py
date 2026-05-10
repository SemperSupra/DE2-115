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

def test_aliasing(wb, port1, port2, name):
    print(f"\n--- Testing Aliasing: {name} (0x{port1:02x} vs 0x{port2:02x}) ---")
    addr1 = USB_BASE + port1
    addr2 = USB_BASE + port2
    
    # Write to port1
    wb.write(addr1, 0x1111)
    
    # Write to port2
    wb.write(addr2, 0x2222)
    
    # Read both back
    # Double read to avoid pipeline delay issues if it's the data port
    _ = wb.read(addr1)
    r1 = wb.read(addr1) & 0xFFFF
    
    _ = wb.read(addr2)
    r2 = wb.read(addr2) & 0xFFFF
    
    print(f"Wrote 0x1111 to 0x{port1:02x}, 0x2222 to 0x{port2:02x}")
    print(f"Read 0x{port1:02x}: 0x{r1:04x}")
    print(f"Read 0x{port2:02x}: 0x{r2:04x}")
    
    if r1 == 0x2222 and r2 == 0x2222:
        print(">>> ALIASING DETECTED! Writing to port 2 overwrote port 1.")
    elif r1 == 0x1111 and r2 == 0x2222:
        print(">>> NO ALIASING. Ports are independent.")
    else:
        print(">>> INCONCLUSIVE. Data not retained or ports are write-only/unresponsive.")

def main():
    wb = RemoteClient()
    wb.open()
    try:
        # Configure Fast Timing
        timing = (6, 2, 2)
        wb.write(BRIDGE_CFG0, hpi_cfg(1, 0, timing[0], timing[1], timing[2]))
        time.sleep(0.5)
        wb.write(BRIDGE_CFG0, hpi_cfg(1, 1, timing[0], timing[1], timing[2]))
        time.sleep(1.0)
        
        print("\n--- Testing Hypothesis: Host A0 -> Chip A1, Chip A0 = 0 ---")
        print("Sequence C: Write Address to 0x4, Data to 0x0")
        wb.write(USB_BASE + 0x4, 0x1000) # Address
        wb.write(USB_BASE + 0x0, 0x9999) # Data
        
        wb.write(USB_BASE + 0x4, 0x1000) # Reset address pointer
        _ = wb.read(USB_BASE + 0x0)
        r0 = wb.read(USB_BASE + 0x0) & 0xFFFF
        print(f"Read 0x00: 0x{r0:04x} (Expected 0x9999 if hypothesis is true)")
        
        print("\nSequence D: Write Address to 0xC, Data to 0x8 (Control group)")
        wb.write(USB_BASE + 0xC, 0x1000)
        wb.write(USB_BASE + 0x8, 0x7777)
        
        wb.write(USB_BASE + 0xC, 0x1000)
        _ = wb.read(USB_BASE + 0x8)
        r8 = wb.read(USB_BASE + 0x8) & 0xFFFF
        print(f"Read 0x08: 0x{r8:04x} (Expected 0x7777)")
        
        print("\nChecking Cross-Aliasing (0x4/0x0 vs 0xC/0x8)")
        wb.write(USB_BASE + 0x4, 0x1000)
        _ = wb.read(USB_BASE + 0x8)
        r8_cross = wb.read(USB_BASE + 0x8) & 0xFFFF
        print(f"Set Address via 0x4, Read Data via 0x8: 0x{r8_cross:04x} (Expected 0x7777 if Host A1 is ignored)")

        
    finally:
        wb.close()

if __name__ == "__main__":
    main()
