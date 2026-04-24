# Project Map

## Top-Level View

### Active Source
- `de2_115_vga_platform.py`
  - Purpose: LiteX platform with verified pin assignments for VGA, Ethernet (Port 1 fixed), and USB (CY7C67200).
- `de2_115_vga_target.py`
  - Purpose: SoC target definition. Includes phase-shifted `eth_tx_ps` clock domain and Wishbone bridge to USB HPI.
- `rtl/vga_text_console.v`
  - Purpose: VGA text generator (80x30). Now uses registered sync for stability.
- `firmware/src/main.c`
  - Purpose: Primary diagnostic and bring-up firmware. Handles LCP/BIOS loading and UART reporting.

### Build & Test Tools
- `scripts/build_firmware.sh`: RISC-V GCC compilation in Docker.
- `scripts/build_soc.sh`: LiteX SoC generation and ROM integration.
- `scripts/build_bitstream.ps1`: Host-side Quartus compilation.
- `scripts/load_bitstream.ps1`: JTAG programming via USB-Blaster.
- `scripts/test_usb_kvm.py`: Automated KVM input test using Epiphan SDK.
- `monitor_uart.py`: Real-time serial diagnostic monitor.

## Development Workflow
1. **Modify Firmware/RTL.**
2. **Rebuild Firmware:** `docker exec litex_env /bin/bash /workspace/scripts/build_firmware.sh`
3. **Regenerate Gateware:** `docker exec litex_env /bin/bash /workspace/scripts/build_soc.sh 1`
4. **Compile SOF:** `.\scripts\build_bitstream.ps1`
5. **Program & Monitor:** `.\scripts\load_bitstream.ps1; python monitor_uart.py`
