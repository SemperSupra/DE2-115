# DE2-115 Handoff - VGA & USB HID Project

## Current Status
*   **Processor:** VexRiscv (RISC-V) implemented via LiteX.
*   **VGA:** **Working.** The `ADV7123` DAC is correctly driven. Sync is active-low, and RGB data is mapped to the correct bits of the counter for a visible test pattern.
*   **USB Hardware:** Conclusively identified as **Cypress CY7C67200** (EZ-OTG). Wishbone-to-HPI bridge is verified working via register/ROM dumps.
*   **USB Driver:** Partially implemented. The firmware successfully reads hardware registers but hangs during the high-level initialization sequence (`Err: t1_2` on LCD).

## Technical Findings
1.  **Chip Identity:** Registers `0xC004` (0x0011), `0xC002` (0x0100), and `0xC008` (0x000F) match the CY7C67200 datasheet defaults exactly.
2.  **Hang Cause:** The Cypress chip requires a proprietary firmware blob (LCP) to be loaded into its internal RAM (address `0x0000`) before it will respond to the `HUSB_SIE1_INIT_INT` (`0x0072`) command. 
3.  **Firmware Source:** The required firmware is located in `DE2_115_demonstrations/DE2_115_NIOS_HOST_MOUSE_VGA/software/DE2_115_NIOS_HOST_MOUSE_VGA/lcp_data.h`.

## Progress
- [x] Corrected VGA pin assignments and DAC timing.
- [x] Corrected USB Data/Address pin mappings for CY7C67200.
- [x] Verified HPI bus communication with VexRiscv.
- [x] Implemented basic TD (Transaction Descriptor) execution engine in C.
- [x] Added diagnostic LCD output for USB status codes.

## Next Steps
1.  **Extract LCP Blob:** Parse `lcp_data.h` to get the binary array.
2.  **Implement Loader:** Add a function to `main.c` that writes this array to `CY_BASE` (Cypress internal memory) using the HPI auto-incrementing data port.
3.  **Boot LCP:** After loading, send the command to start LCP execution.
4.  **Resume Enumeration:** Once LCP is running, the existing `cy7c67200_init()` logic should receive the `COMM_ACK` and proceed to detect the Epiphan KVM2USB device.
5.  **Verify HID:** Use the `E1` polling loop to display HID usage codes on the LCD.
