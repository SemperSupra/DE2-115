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

def test_cpu_flags(wb):
    HPI_ADDRESS = USB_BASE + 0xC
    HPI_DATA = USB_BASE + 0x8
    
    print("\n--- Testing CPU_FLAGS_REG (0xC000) ---")
    # Read current flags
    wb.write(HPI_ADDRESS, 0xC000)
    _ = wb.read(HPI_DATA)
    flags = wb.read(HPI_DATA) & 0xFFFF
    print(f"Initial CPU Flags: 0x{flags:04x}")
    
    # Try to halt CPU (Bit 0 is CPU_RUN? Actually, let's write a pattern and read back)
    wb.write(HPI_ADDRESS, 0xC000)
    wb.write(HPI_DATA, 0x1234)
    
    wb.write(HPI_ADDRESS, 0xC000)
    _ = wb.read(HPI_DATA)
    r1 = wb.read(HPI_DATA) & 0xFFFF
    print(f"Wrote 0x1234, Read: 0x{r1:04x}")
    
    wb.write(HPI_ADDRESS, 0xC004) # HW Rev
    _ = wb.read(HPI_DATA)
    rev = wb.read(HPI_DATA) & 0xFFFF
    print(f"HW Revision (0xC004): 0x{rev:04x}")

def main():
    wb = RemoteClient()
    wb.open()
    try:
        timing = (6, 2, 2)
        wb.write(BRIDGE_CFG0, hpi_cfg(1, 0, timing[0], timing[1], timing[2]))
        time.sleep(0.5)
        wb.write(BRIDGE_CFG0, hpi_cfg(1, 1, timing[0], timing[1], timing[2]))
        time.sleep(0.5)
        
        test_cpu_flags(wb)
    finally:
        wb.close()

if __name__ == "__main__":
    main()
