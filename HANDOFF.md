# DE2-115 Handoff - Status Update

Date: 2026-04-24
Workspace: `C:\Users\Mark\Projects\DE2-115`

## Executive Status
- **Serial Connection Established:** UART (COM3) is now fully integrated and functional at 115200 baud. It provides real-time heartbeat and co-processor diagnostics.
- **VGA Stabilized:** Registering sync signals has fixed VGA capture issues.
- **USB HPI Bridge Functional:** The Wishbone-to-HPI bridge is 100% verified for data integrity.
- **Ethernet Physical Link Solid:** Both PHYs show Link UP, but IP connectivity is still pending.

## Technical Progress

### 1. UART & Diagnostics
- Integrated `UART` peripheral at pins `G9`/`G12`.
- Updated `firmware/src/main.c` with a robust diagnostic suite that reports:
  - System Ticks
  - PHY Link Status (Both Ports)
  - USB Co-processor Revision and Status
  - Raw HID endpoint data

### 2. USB Subsystem Bring-up
- **Resolved Pin Conflicts:** Removed `dack_n` (unused) which was conflicting with `addr[1]` on pin `C14`.
- **HPI Timing:** Optimized bridge timing with `CY_BRIDGE_CFG0` (20 access cycles).
- **Firmware Loading:** Implemented full LCP and BIOS loading sequence.
- **Current State:** The hardware interface is verified. The co-processor is alive and H1STAT shows `0x003C` (Device Detected), but a final "Connected" handshake via mailbox is still being tuned.

### 3. VGA Subsystem Fixes
- Registered `vga_hsync_n` and `vga_vsync_n` in `rtl/vga_text_console.v`.
- This ensures zero-glitch sync pulses perfectly aligned with the pixel clock.

## Current Blockers / Open Issues
- **Ethernet ARP/IP:** Despite PHY link UP at 1000Mbps, the host cannot ping the board. Suspect RGMII TX skew or MAC filtering.
- **USB Device Handshake:** co-processor detects device hardware-wise but doesn't transition to the "CONNECTED" software state in the mailbox.

## Next Steps
1. **Debug Ethernet TX Path:** Use SignalTap to verify if RGMII TX data is actually reaching the pins with correct timing.
2. **Refine USB Handshake:** Verify the BIOS/LCP jump addresses and ensure co-processor IRQs are handled or polled correctly.
3. **KVM Validation:** Once "CONNECTED" state is reached, run `scripts/test_usb_kvm.py` to exercise the HID stack.

## Useful Commands
```powershell
# Full Build Cycle (Firmware -> SoC -> Bitstream -> Load)
docker exec litex_env /bin/bash /workspace/scripts/build_firmware.sh
docker exec litex_env /bin/bash /workspace/scripts/build_soc.sh 1
.\scripts\build_bitstream.ps1
.\scripts\load_bitstream.ps1

# Run Diagnostics Monitor
python monitor_uart.py

# Run KVM Automated Test
python scripts/test_usb_kvm.py
```
