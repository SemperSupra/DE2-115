import time
import itertools
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

def test_rw(wb, data_off, mailbox_off, address_off, status_off, timing):
    wb.write(BRIDGE_CFG0, hpi_cfg(1, 0, timing[0], timing[1], timing[2]))
    time.sleep(0.01)
    wb.write(BRIDGE_CFG0, hpi_cfg(1, 1, timing[0], timing[1], timing[2]))
    time.sleep(0.05)
    
    HPI_STATUS = USB_BASE + status_off
    HPI_MAILBOX = USB_BASE + mailbox_off
    HPI_DATA = USB_BASE + data_off
    HPI_ADDRESS = USB_BASE + address_off
    
    test_val = 0x1234
    test_val2 = 0x5678
    
    # Try RAM R/W
    wb.write(HPI_ADDRESS, 0x1000)
    wb.write(HPI_DATA, test_val)
    
    wb.write(HPI_ADDRESS, 0x1000)
    _ = wb.read(HPI_DATA) & 0xFFFF
    r1_actual = wb.read(HPI_DATA) & 0xFFFF
    
    wb.write(HPI_ADDRESS, 0x1000)
    wb.write(HPI_DATA, test_val2)
    
    wb.write(HPI_ADDRESS, 0x1000)
    _ = wb.read(HPI_DATA) & 0xFFFF
    r2_actual = wb.read(HPI_DATA) & 0xFFFF
    
    return r1_actual, r2_actual

def main():
    wb = RemoteClient()
    wb.open()
    try:
        offsets = [0x0, 0x4, 0x8, 0xC]
        perms = list(itertools.permutations(offsets))
        timing = (6, 2, 2)
        
        print("Testing all permutations for RAM R/W (expected: 0x1234, 0x5678)...")
        for i, p in enumerate(perms):
            data_off, mailbox_off, address_off, status_off = p
            r1, r2 = test_rw(wb, data_off, mailbox_off, address_off, status_off, timing)
            if r1 != 0x0000 or r2 != 0x0000:
                print(f"Index {i:02d} (data={data_off:x}, mailbox={mailbox_off:x}, address={address_off:x}, status={status_off:x}): Readback 1=0x{r1:04x}, Readback 2=0x{r2:04x}")
                if r1 == 0x1234 and r2 == 0x5678:
                    print("  *** PERFECT MATCH ***")
                    
    finally:
        wb.close()

if __name__ == "__main__":
    main()
