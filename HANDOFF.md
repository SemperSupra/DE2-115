# Session Handoff

Date: 2026-05-10
Branch: `ethernet-baseline-shim`

## The Journey So Far
This session was highly productive but ended with a profound hardware mystery.

1.  **The HPI Breakthrough:** We successfully recovered and proved the logic to talk to the CY7C67200 over the HPI bus. It requires a "Pulse Fix" in `rtl/cy7c67200_wb_bridge.v` (RD/WR strobes must be inside the CS window) and "Fast Timing" (access=6 cycles).
2.  **The Golden Unified Image:** Previous attempts to integrate the USB fixes caused Ethernet timing regressions. We abandoned automated LiteX generation and executed a "Hardware Shim" strategy. We took the known-good April 27th Quartus project, manually updated the physical pin assignments to match the exact 2.5V/3.3V board banks, and inserted the fixed RTL. **This succeeded.** We now have a stable bitstream with 100% reliable Ethernet and the new USB logic.
3.  **The LCP Handshake Failure:** With the bus proven, we attempted Rung 2 of the bring-up ladder: The LCP Handshake. It timed out. The chip received the `0xFA50` reset command but never set the `ACK` bit in the Status register.
4.  **The Aliasing Anomaly:** Exhaustive diagnostic scripts (`test_a0_stuck.py`, `test_ram_boot.py`, `test_c000_alias.py`) revealed a catastrophic issue. The CY7C67200 is treating the HPI bus like a small, wrapping chunk of RAM. Writing to address `0xC000` (the CPU Flags register) actually writes to RAM address `0x0000`. The upper address bits are either being ignored by the chip, or our FPGA pins are not driving them correctly.

## The Blocker
Because of the address aliasing, **the internal registers of the CY7C67200 are physically inaccessible.** 
- We cannot access the Mailbox or Status registers to perform the LCP Handshake.
- We cannot access the CPU Control registers to halt the processor and perform a Direct RAM Boot.

## Next Actions for Next Session
The software abstraction layer (Etherbone -> Wishbone -> HPI Bridge) has given us all the information it can. The next required step is a **SignalTap Hardware Capture**.

1.  **Compile SignalTap:** The QSF in `build\terasic_de2_115\gateware\` has been prepped to include `signaltap/usb_hpi_capture.stp`, but that compilation failed previously due to missing nodes or routing issues. You must successfully compile a bitstream that includes the SignalTap logic analyzer probing `usb_otg_data`, `usb_otg_addr`, and the control strobes.
2.  **Capture Raw Pins:** Trigger the logic analyzer while running one of the diagnostic Python scripts (like `test_c000_alias.py`).
3.  **Analyze the Truth:** The `.vcd` trace will definitively prove whether the FPGA is actually driving the `OTG_ADDR` and `OTG_DATA` pins with the correct values, or if the CY7C67200 is ignoring them.

## Important Files
*   `docs/HPI_BREAKTHROUGH_REPORT.md`: Details of the Pulse Fix and Timing.
*   `docs/DEVICE_BRINGUP_LADDER.md`: The full bring-up plan (currently stuck at Rung 2).
*   `FINDINGS.md`: Detailed logs of the aliasing anomaly.
*   `build\terasic_de2_115\gateware\de2_115_vga_platform.qsf`: The "Golden" Quartus settings file that maintains Ethernet stability. Do NOT let LiteX overwrite this.
*   `scripts/test_*.py`: A suite of HPI diagnostic scripts used to prove the aliasing.