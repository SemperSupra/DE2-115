import time
from litex import RemoteClient
from cy7c67200_hpi import PORT_MAPS, TIMING_PROFILES, hpi_cfg, BRIDGE_CFG0

def dump_hpi():
    wb = RemoteClient(port=1235)
    wb.open()
    
    tp = TIMING_PROFILES["slow"]
    
    # Reset cycle
    wb.write(BRIDGE_CFG0, hpi_cfg(1, 0, tp.access_cycles, tp.sample_offset, tp.turnaround_cycles))
    time.sleep(0.1)
    wb.write(BRIDGE_CFG0, hpi_cfg(1, 1, tp.access_cycles, tp.sample_offset, tp.turnaround_cycles))
    time.sleep(0.5)
    
    USB_BASE = 0x82000000
    
    print("Dumping HPI Registers (offsets 0, 4, 8, C):")
    for i in range(4):
        addr = USB_BASE + (i * 4)
        val = wb.read(addr) & 0xFFFF
        print(f"Offset 0x{i*4:x}: 0x{val:04x}")
        
    print("\nWriting 0x1234 to Address Reg (Offset 8)...")
    wb.write(USB_BASE + 0x8, 0x1234)
    
    print("Dumping HPI Registers again:")
    for i in range(4):
        addr = USB_BASE + (i * 4)
        val = wb.read(addr) & 0xFFFF
        print(f"Offset 0x{i*4:x}: 0x{val:04x}")

    wb.close()

if __name__ == "__main__":
    dump_hpi()
