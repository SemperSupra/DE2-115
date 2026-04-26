# Project Map

## Active Source

- `de2_115_vga_platform.py`
  - LiteX platform extensions for VGA, Ethernet, USB OTG, LCD, LEDs, and 7-segment displays.
  - Adds `eth_gtx_clocks` so RGMII gigabit TX clock uses the dedicated GTX pins instead of the base LiteX TX_CLK resources.
  - USB OTG pin assignments match Terasic QSF references for data, address, control, reset, interrupt pins, and DREQ0; unverified DACK pins are intentionally not assigned.
- `de2_115_vga_target.py`
  - Main LiteX SoC target.
  - Ethernet Port 1 is now the default.
  - The current working Ethernet image forces the RGMII PHY wrapper into MII/10-100 operation for stability; gigabit is deferred.
  - Instantiates LiteEth RGMII, Etherbone, VGA text console, USB HPI bridge, and LiteScope analyzers.
- `isp1761.py`
  - Python/Migen wrapper around the external CY7C67200 HPI bridge.
  - Name is historical; the hardware is CY7C67200, not ISP1761.
- `cy7c67200_wb_bridge.v`
  - Wishbone-to-CY7C67200 HPI bridge.
  - Performs local USB-window address decode, reset/timing config, access stretching, debug register reporting, and HPI transaction sequencing.
- `CY7C67200_IF.v`
  - Registered Terasic-style HPI pad wrapper.
  - Registers address/control/data and tri-states `HPI_DATA` on reads.
- `rtl/`
  - Staged copies of custom RTL. Keep root-level and `rtl/` bridge files synchronized until the source flow is cleaned up.
- `firmware/src/main.c`
  - Primary bring-up firmware.
  - Handles MDIO delay setup, PHY diagnostics, LiteEth MAC diagnostics, HPI reset/timing configuration, USB memory tests, LCP/BIOS loading attempts, and UART reporting.

## Documentation

- `README.md`
  - High-level project state and build flow.
- `HANDOFF.md`
  - Current board-tested handoff, latest UART evidence, and next steps.
- `FINDINGS.md`
  - Evidence-based findings and blockers.
- `ETHERNET_BASELINE.md`
  - Preservation manifest for the working Ethernet Port 1 low-speed baseline.
- `DEVICE_STATUS_AND_BRINGUP.md`
  - Full DE2-115 device matrix, current status, pass criteria, and staged
    bring-up strategy for remaining peripherals.
- `EXECUTION_PLAN.md`
  - Prioritized engineering plan.
- `SIGNALTAP_STRATEGY.md`
  - Debug methodology.
- `DE2_115_SIGNALTAP_IMPLEMENTATION_PLAN.md`
  - Concrete SignalTap capture targets.

## Build & Test Tools

- `scripts/build_firmware.sh`
  - Builds RISC-V firmware in Docker. Accepts `FIRMWARE_CFLAGS`, including `-DDE2_ETH_SPEED_MODE=100` and `-DDE2_ETH_SPEED_MODE=10`.
- `scripts/build_soc.sh`
  - Regenerates the LiteX SoC and integrates firmware into ROM. Defaults to Ethernet Port 1.
- `scripts/ethernet_low_speed_test.py`
  - Low-speed Ethernet regression: Windows ping, `litex_server`, LiteX identifier read, and LED CSR write/read stress.
- `scripts/load_bitstream.ps1`
  - Programs the board through USB-Blaster.
- `scripts/test_usb_kvm.py`
  - Future KVM/HID test hook; blocked until CY7C67200 HPI readback works.
- `monitor_uart.py`
  - Serial diagnostic monitor.
- `validation_images/`
  - Git-tracked known-good `.sof` files. Currently includes the 2026-04-26
    Port 1 10 Mbps Ethernet validation image.

## Verified Workflow

```powershell
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_firmware.sh'
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_soc.sh 1'
```

```powershell
C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_sh.exe --flow compile de2_115_vga_platform
```

Run Quartus from:

```powershell
C:\Users\Mark\Projects\DE2-115\build\terasic_de2_115\gateware
```

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\load_bitstream.ps1
```

## Current Debug Focus

- **USB:** Prove why CY7C67200 does not drive nonzero read data during HPI read cycles.
- **Ethernet:** Keep forced-MII Port 1 as the working baseline; AUTO10/100, 100-only, and 10-only ping plus Etherbone CSR stress now pass.
- **Next device:** SD card, once USB is either fixed or explicitly paused.

- `signaltap/`
  - Repo-tracked Quartus SignalTap session files for USB HPI and Ethernet RGMII.

Host-side SignalTap collection:

```powershell
C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_stp.exe -t scripts\run_capture.tcl signaltap\usb_hpi_capture.stp local_artifacts\signaltap\usb_hpi_capture.csv
C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_stp.exe -t scripts\run_capture.tcl signaltap\eth_rgmii_capture.stp local_artifacts\signaltap\eth_rgmii_capture.csv
```
