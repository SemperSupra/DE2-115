# DE2-115 VGA and USB HID Bring-Up

This repository is a board bring-up project for the Terasic DE2-115 FPGA board.
It builds a LiteX SoC around a VexRiscv CPU, drives VGA directly, exposes board
status devices such as LEDs, 7-segment displays, and the LCD, and is intended to
use the onboard USB OTG controller as a host for an external HID-class device.

## Current State

- VGA output is working with a custom 640x480 test-pattern generator.
- The external USB controller bus is mapped and readable from firmware.
- The active blocker is USB controller initialization: the firmware reaches the
  `Err: t1_2` path because the CY7C67200 needs its internal LCP firmware loaded
  before `HUSB_SIE1_INIT_INT` will acknowledge.

## Important Files

- `HANDOFF.md`: latest bring-up handoff and immediate next steps.
- `FINDINGS.md`: repository-level findings from code and artifact inspection.
- `PROJECT_MAP.md`: directory map, file roles, and suggested workflow.
- `de2_115_vga_platform.py`: DE2-115 pin mapping extensions.
- `de2_115_vga_target.py`: LiteX SoC definition.
- `isp1761.py`: Wishbone-to-external HPI bridge.
- `firmware/src/main.c`: firmware bring-up logic and USB transaction code.

## Build Flow

1. Generate/build the SoC from `de2_115_vga_target.py`.
2. Build firmware in `firmware/src`.
3. Rebuild the SoC with the firmware binary integrated into ROM.
4. Program the `.sof` bitstream to the board.

Helper scripts for host setup, firmware build, SoC build, and programming are in
`scripts/`.

## Immediate Engineering Goal

Extract the LCP blob from the Terasic demonstration sources, load it into the
CY7C67200 over HPI from firmware, then resume the existing USB enumeration path.
