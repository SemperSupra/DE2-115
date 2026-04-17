# DE2-115 Handoff - Ethernet & USB Status

Date: 2026-04-16  
Workspace: `C:\Users\Mark\Projects\DE2-115`

## Executive Status

- **MDIO Management is 100% Resolved:** Sampling edge fixed in firmware; 100% reliable register access to PHYs at addr 16 and 17.
- **USB Bridge is 100% Fixed:** Resolved address decoding bug in `rtl/cy7c67200_wb_bridge.v`. Bridge is now fully configurable at runtime.
- **Ethernet Status:** Physical link is UP (LEDs D1, D20 solid), but PHY Register 1 still reports Link Down. In-band status enabled and reporting 1000Mbps.
- **USB Status:** Strapping pins verified; chip remains unresponsive. Now ready for timing sweeps.

## Technical Progress

### 1. Pinout & Strapping
- Corrected on-board PHY pins and verified reset toggling.
- USB strapping now correctly drives `DACK#` (HIGH) and `DREQ` (LOW).

### 2. Diagnostic Tools
- **HPI Analyzer:** Custom 160-bit probe in `rtl/cy7c67200_wb_bridge.v` for JTAG capture.
- **VGA OCR:** `read_vga.py` decodes real-time diagnostics from the screen.
- **Probe Decoder:** `decode_probe.py` updated to support real-time pipe from `quartus_stp`.

### 3. Firmware Improvements
- MDIO sampling adjusted to remove bit-shift.
- RGMII in-band status enabled in Marvell PHY.
- Added MDIO address scanner to VGA console.
- Corrected USB bridge register offsets (`0x100` instead of `0x500`).

## Current Blockers / Open Issues

- **Ethernet Link Logic:** PHY is not asserting the link bit to the SoC despite physically sensing a link. Likely a mode conflict (Fiber vs. Copper).
- **USB Responsiveness:** CY7C67200 still silent. Needs timing sweeps using the now-functional bridge configuration registers.

## Next Steps

1.  **Ethernet Force Mode:** Modify firmware to force PHY into 1000Mbps Full-Duplex (disabling Auto-Neg) and check Link bit.
2.  **USB Timing Sweep:** Use `CY_BRIDGE_CFG0` at runtime to sweep `ACCESS_CYCLES` (6-63) and `SAMPLE_OFFSET`.

## Useful Commands

```powershell
# Automated Status Check
py -3.12 observe_vga.py; py -3.12 read_vga.py

# HPI Bus Trace
& "C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_stp.exe" -t scripts/read_captured_hpi.tcl
py -3.12 decode_probe.py
```
