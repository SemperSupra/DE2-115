# DE2-115 Handoff - Status Update

Date: 2026-04-25
Workspace: `C:\Users\Mark\Projects\DE2-115`

## Executive Status
- **Serial Connection Established:** UART (COM3) is fully functional for diagnostics.
- **VGA Stabilized:** Sync signals registered for improved capture stability.
- **USB HPI Bridge:** Hardware verified. Firmware loading (LCP/BIOS) and host initialization implemented.
- **Ethernet:** Physical link (1000Mbps) established on Port 1. IP connectivity issue remains.

## Technical Progress
- **USB:** Fixed HPI address map, stabilized timing, and added robust device detection logic.
- **Ethernet:** Implemented RGMII delay calibration via MDIO and verified TX clock alignment.
- **Instrumentation:** Added `eth_analyzer` (LiteEth MAC) and `hpi_analyzer` (HPI bus) for deeper debugging.

## Next Steps
1. **Analyze Ethernet Trace:** Use `litescope_cli` to inspect MAC-layer traffic for ARP packets.
2. **Debug USB Handshake:** Verify co-processor firmware mailbox message transitions.

## Useful Commands
```powershell
# Build Cycle
docker exec litex_env /bin/bash /workspace/scripts/build_firmware.sh
docker exec litex_env /bin/bash /workspace/scripts/build_soc.sh 1
.\scripts\build_bitstream.ps1
.\scripts\load_bitstream.ps1

# Run Diagnostics
python monitor_uart.py
```
