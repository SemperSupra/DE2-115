#!/usr/bin/env python3
import time
from litex import RemoteClient
from cy7c67200_hpi import CyHpi, PORT_MAPS, TIMING_PROFILES, hpi_cfg, BRIDGE_CFG0

def trigger():
    wb = RemoteClient(port=1234)
    wb.open()
    
    # Use slow timing profile
    pm = PORT_MAPS["canonical"]
    tp = TIMING_PROFILES["slow"]
    
    # Perform a hard reset pulse
    print("Asserting Hardware Reset...")
    # force_rst=1, rst_n=0
    wb.write(BRIDGE_CFG0, hpi_cfg(1, 0, tp.access_cycles, tp.sample_offset, tp.turnaround_cycles))
    time.sleep(0.1)
    
    print("Releasing Hardware Reset...")
    # force_rst=1, rst_n=1
    wb.write(BRIDGE_CFG0, hpi_cfg(1, 1, tp.access_cycles, tp.sample_offset, tp.turnaround_cycles))
    time.sleep(0.5) # Give it plenty of time to boot BIOS
    
    cfg_rb = wb.read(BRIDGE_CFG0)
    print(f"Readback BRIDGE_CFG0: 0x{cfg_rb:08x}")
    
    hpi = CyHpi(wb, pm)
    
    print("Triggering HPI Read from offset 0x0...")
    val = wb.read(hpi._addr(pm.data))
    print(f"Read value: 0x{val:04x}")
    
    print("Triggering HPI Write to offset 0x8 (Address Register)...")
    wb.write(hpi._addr(pm.address), 0x1234)
    
    print("Triggering HPI Read from offset 0x8 (Address Register)...")
    val = wb.read(hpi._addr(pm.address))
    print(f"Read value: 0x{val:04x}")

    wb.close()

if __name__ == "__main__":
    trigger()
