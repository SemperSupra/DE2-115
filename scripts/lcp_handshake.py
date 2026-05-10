import time
from litex import RemoteClient

USB_BASE = 0x82000000
BRIDGE_CFG0 = USB_BASE + 0x100

COMM_RESET = 0xFA50
COMM_ACK   = 0x0FED

def hpi_cfg(force_rst, rst_n, access, sample, turnaround):
    return (
        (force_rst & 1)
        | ((rst_n & 1) << 1)
        | ((access & 0x3F) << 2)
        | ((sample & 0x3F) << 8)
        | ((turnaround & 0x3F) << 14)
    )

def test_handshake_broadcast(wb, timing):
    print(f"\n--- Testing Broadcast Handshake ---")
    wb.write(BRIDGE_CFG0, hpi_cfg(1, 0, timing[0], timing[1], timing[2]))
    time.sleep(1.0)
    wb.write(BRIDGE_CFG0, hpi_cfg(1, 1, timing[0], timing[1], timing[2]))
    time.sleep(2.0)
    
    ports = [0x0, 0x4, 0x8, 0xC]
    
    print("Initial state of all ports:")
    for p in ports:
        _ = wb.read(USB_BASE + p)
        v = wb.read(USB_BASE + p) & 0xFFFF
        print(f"Port 0x{p:02x}: 0x{v:04x}")
        
    print(f"\nBroadcasting COMM_RESET (0x{COMM_RESET:04x}) to ALL ports...")
    for p in ports:
        wb.write(USB_BASE + p, COMM_RESET)
        
    print("Polling all ports for changes or ACK...")
    timeout = time.time() + 3.0
    last_vals = {p: 0x0000 for p in ports}
    
    while time.time() < timeout:
        for p in ports:
            _ = wb.read(USB_BASE + p)
            v = wb.read(USB_BASE + p) & 0xFFFF
            if v != last_vals[p] and v != 0x0000 and v != 0xFFFF:
                print(f"Port 0x{p:02x} changed to: 0x{v:04x}")
                last_vals[p] = v
            if v == COMM_ACK:
                print(f"!!! LCP Handshake SUCCESS on Port 0x{p:02x} !!!")
                return True
        time.sleep(0.05)
    print("Broadcast Handshake TIMEOUT.")
    return False

def main():
    wb = RemoteClient()
    wb.open()
    try:
        timing = (6, 2, 2)
        test_handshake_broadcast(wb, timing)
    finally:
        wb.close()

if __name__ == "__main__":
    main()
