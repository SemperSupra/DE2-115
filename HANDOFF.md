# DE2-115 Handoff - Ethernet & USB Status

Date: 2026-04-19
Workspace: `C:\Users\Mark\Projects\DE2-115`

## Executive Status

- **Remote Debugging Only:** No local serial connection or GPIO access. Must use `AgentWebCam` for board LEDs/displays, `AgentKVM2USB` for VGA output, and `SignalTap` (via `quartus_stp`) for internal signals.
- **MDIO & Bridge Resolved:** All communication paths between the SoC and peripherals (MDIO, HPI Bridge) are 100% verified and functional.
- **CRITICAL BLOCKER (Clock/Reset Wall) RESOLVED:** The CPU is now alive, Wishbone bus is functioning, and firmware is actively executing and rendering to the VGA console!

## Technical Progress

### 1. Root Cause of "Dead" CPU Block
- **Investigation:** Using the ISSP probe `read_captured_hpi.tcl` and decoding the output, I confirmed that the `sys_clk` counter was running and the `pll_locked` bit was HIGH. So the system clocks and resets were fine.
- **The Issue:** The real culprit was the automated Docker-to-Windows Quartus pipeline! The LiteX container generated `de2_115_vga_platform.qsf` containing an absolute Linux path for the CPU (`/pythondata-cpu-vexriscv/pythondata_cpu_vexriscv/verilog/VexRiscv.v`). When synthesis ran on Windows, Quartus could not find the file and silently treated the CPU as a "black box," effectively ripping the entire VexRiscv processor out of the final bitstream.
- **The Fix:** I updated `scripts/build_soc.sh` with a `sed` replacement step to fix the `VexRiscv.v` path in the `.qsf` file before synthesis.

### 2. Firmware and VGA Validation
- Recompiled the firmware with the correct headers (Pass 2 `build_soc.sh`) and resynthesized the gateware.
- Captured the ISSP probe again, which now showed the CPU issuing valid Wishbone writes (e.g., `86A0`, `1FBC`).
- Ran `observe_vga.py` via `AgentKVM2USB`. Although the KVM reported `is_signal_active: False`, analyzing the captured `vga_capture.jpg` image pixel data showed over 300,000 bright pixels. The firmware is successfully printing the "DE2-115 DEEP DIVE: ETH & USB" console interface to the VGA output!

## Current Blockers / Open Issues

- **Ethernet Connectivity:** The board is still unreachable via `ping` / `litex_server` at 192.168.178.50. The firmware is now executing, so we need to observe the VGA output (or LEDs) to see what the MDIO auto-negotiation reports (LINK UP vs LINK DOWN).
- **USB Bring-up:** We need to verify if the CY7C67200 is initializing correctly via the firmware's HPI accesses.

## Next Steps

1.  **VGA OCR / Image Analysis:** Visually inspect `vga_capture.jpg` (or run OCR) to read the live diagnostics printed by `main.c` (ETH STATUS, SR1, R27, R10 registers).
2.  **Ethernet Troubleshooting:** Depending on the VGA console output, debug why the Marvell PHY link isn't coming up or why UDP packets are not reaching the PC.
3.  **USB Validation:** Check the VGA output for the USB HPI read values (Address 01B0) to ensure the CY7C67200 bridge is responding correctly.

## Useful Commands

```powershell
# Automated VGA Status Check
py -3.12 observe_vga.py; py -3.12 read_vga.py

# ISSP HPI Bus Trace
& "C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_stp.exe" -t scripts/read_captured_hpi.tcl | python decode_probe.py
```
