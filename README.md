# DE2-115 VGA, Ethernet, and USB HID Bring-Up

This repository is a board bring-up project for the Terasic DE2-115 FPGA board.
It builds a LiteX SoC around a VexRiscv CPU, drives VGA directly, exposes board
status devices such as LEDs, 7-segment displays, and the LCD, and is intended to
use the onboard CY7C67200 USB OTG controller as a host for an external HID-class
device.

## Current State

- VGA output is working.
- UART diagnostics are working on COM3 at 115200 baud.
- Ethernet Port 1 is the default. PHY17 responds over MDIO and the forced-MII
  10/100 path is now the validated network baseline. AUTO10/100, 100-only, and
  10-only firmware variants each passed 50/50 ping to `192.168.178.50` plus 512
  Etherbone red-LED CSR write/read loops through `litex_server` on host TCP port
  `1235`. Gigabit mode is intentionally deferred to the backlog.
- USB HPI register ordering, local address decode, and unverified DACK pin
  assignment have been fixed. The FPGA now drives HPI write data correctly,
  confirmed by debug readback showing `sample=00001234 cy=00001234` during a
  write cycle.
- The active USB blocker is HPI readback from the CY7C67200. All CY register and
  memory reads currently return `0x0000`, so the LCP memory check, LCP ACK, and
  later SIE host initialization cannot complete. A host-driven Etherbone timing
  sweep after CY reset release also returned only zeroes, so this is not a
  simple HPI sample-offset issue.

## Important Files

- `HANDOFF.md`: latest bring-up handoff and immediate next steps.
- `FINDINGS.md`: current evidence and open blockers.
- `PROJECT_MAP.md`: directory map, file roles, and suggested workflow.
- `de2_115_vga_platform.py`: DE2-115 pin mapping extensions.
- `de2_115_vga_target.py`: LiteX SoC definition and Ethernet/USB integration.
- `isp1761.py`: Wishbone wrapper for the CY7C67200 HPI bridge.
- `cy7c67200_wb_bridge.v`: Wishbone-to-HPI bridge.
- `CY7C67200_IF.v`: registered HPI pad wrapper based on the Terasic reference.
- `firmware/src/main.c`: diagnostic firmware, MDIO setup, HPI tests, and USB bring-up logic.
- `validation_images/`: tracked known-good `.sof` images. The current saved
  image is the Port 1 10 Mbps Ethernet validation build.

## Build Flow

1. Build firmware in Docker.
2. Regenerate the SoC with Ethernet Port 1 and firmware integrated into ROM.
3. Compile the Quartus project on the Windows host.
4. Program the `.sof` bitstream to the board.
5. Capture UART output from COM3.

Verified commands:

```powershell
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_firmware.sh'
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_soc.sh 1'
```

Low-speed Ethernet firmware variants:

```powershell
docker compose exec -T litex_builder /bin/bash -lc 'FIRMWARE_CFLAGS=-DDE2_ETH_SPEED_MODE=100 /workspace/scripts/build_firmware.sh'
docker compose exec -T litex_builder /bin/bash -lc 'FIRMWARE_CFLAGS=-DDE2_ETH_SPEED_MODE=10 /workspace/scripts/build_firmware.sh'
```

```powershell
C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_sh.exe --flow compile de2_115_vga_platform
```

Run Quartus from:

```powershell
C:\Users\Mark\Projects\DE2-115\build\terasic_de2_115\gateware
```

Program:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\load_bitstream.ps1
```

Low-speed Ethernet regression:

```powershell
python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235
```

The tracked 10 Mbps validation image is:

```text
validation_images/de2_115_vga_platform_eth10_validated_20260426.sof
SHA256 B886FAC43010C039237CBC94BE316AEF1796E6496DE63DEAD67AFB032FB9373A
```

## Local Artifact Policy

Runtime artifacts such as screenshots, videos, subtitles, and host logs are kept
under `local_artifacts/` for local use and are intentionally excluded from git.

Large local reference trees such as `DE2_115_demonstrations/` and nested external
repositories under `tools/` are also treated as local-only in this clone. That
exclude policy currently lives in `.git/info/exclude`, so future clones should
apply the same local excludes unless those trees are intentionally vendored into
the repository.

## Immediate Engineering Goal

Resolve the remaining USB electrical/protocol boundary failure and then broaden
peripheral coverage:

- Ethernet: keep AUTO10/100, 100-only, and 10-only passing with the regression
  script before changing USB or other timing-sensitive logic.
- USB: after Ethernet remains stable, prove why the CY7C67200 does not drive
  nonzero data during HPI read cycles.
- Gigabit Ethernet: deferred backlog item; do not mix it with the current USB
  debug path.
- Next target after Ethernet/USB: SD card, because LiteSDCard is already
  instantiated and block storage gives a high-value, deterministic test target.

SignalTap captures must be run from an elevated Windows PowerShell on the host,
not from Docker:

```powershell
C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_stp.exe -t scripts\run_capture.tcl signaltap\usb_hpi_capture.stp local_artifacts\signaltap\usb_hpi_capture.csv
C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_stp.exe -t scripts\run_capture.tcl signaltap\eth_rgmii_capture.stp local_artifacts\signaltap\eth_rgmii_capture.csv
```
