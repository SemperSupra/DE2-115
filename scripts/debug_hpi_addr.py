import time
from litex import RemoteClient

USB_BASE = 0x82000000
BRIDGE_CFG0 = USB_BASE + 0x100
LAST_CTRL = USB_BASE + 0x104

def debug():
    wb = RemoteClient()
    wb.open()
    
    print("Reading Data Reg (offset 0x0)...")
    wb.read(USB_BASE + 0x0)
    
    ctrl = wb.read(LAST_CTRL)
    print(f"LAST_CTRL after offset 0x0: 0x{ctrl:08x}")
    
    # Bits 14:13 are hpi_addr
    addr = (ctrl >> 13) & 0x3
    print(f"Captured hpi_addr: {addr}")
    
    print("Reading Address Reg (offset 0x8)...")
    wb.read(USB_BASE + 0x8)
    
    ctrl = wb.read(LAST_CTRL)
    print(f"LAST_CTRL after offset 0x8: 0x{ctrl:08x}")
    
    addr = (ctrl >> 13) & 0x3
    print(f"Captured hpi_addr: {addr}")
    
    wb.close()

if __name__ == "__main__":
    debug()
