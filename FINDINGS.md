# Findings

Date: 2026-05-16

## Current Status

- **CPU/UART:** VexRiscv firmware is executing and UART diagnostics are reliable on COM3 at 115200 baud.
- **VGA:** Working.
- **Ethernet:** Port 1 is stable at 10/100 Mbps.
- **7-Segment Display:** Logic inverted to active-low in `de2_115_vga_target.py` to match DE2-115 hardware.
- **USB HPI (CY7C67200):** **LOGICAL TIMING BLOCKER.**
    - **Hardware Validated:** Swapped to a second DE2-115 board (Board B); failure mode was identical (0x0000 readback). This definitively disproves the "Stuck Pin H7" hypothesis.
    - **Internal Logic:** LiteScope confirms that internal FPGA signals are toggling correctly.
    - **Refactor:** Implemented `STATE_SETUP` in the HPI bridge (2-cycle address stability) and 4-cycle explicit tri-stating on the data bus to resolve potential contention/setup violations.

## Root Cause Analysis (Revised)

The 0x0000 readback is caused by a timing mismatch between the FPGA's asynchronous HPI bridge and the CY7C67200 chip. Specifically, the chip requires the address to be stable before Chip Select falls, and the FPGA must not drive the data bus during the chip's turn-around time.

## Recommended Next Steps

1.  **Regenerate SoC:** Run `./scripts/build_soc.sh 1` to integrate the latest RTL and 7-segment fixes into the top-level.
2.  **Full Compile:** Perform a clean Quartus build.
3.  **HPI Validation:** Run `scripts/trigger_hpi.py` to verify `HPI_CHIP_ID` (0x0011).
