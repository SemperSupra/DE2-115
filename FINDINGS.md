# Findings

## Repository Purpose

This project is a DE2-115 FPGA board bring-up effort centered on a custom LiteX
SoC. It combines:

- LiteX + VexRiscv for the soft CPU and memory map.
- A custom VGA path that bypasses the heavier LiteX video cores.
- Firmware-driven control of LEDs, switches, 7-segment displays, and LCD.
- A memory-mapped bridge from the CPU to the board's USB OTG controller.

## Confirmed Architecture

- The SoC is defined in `de2_115_vga_target.py`.
- Board-specific pin mappings are added in `de2_115_vga_platform.py`.
- The USB interface is presented to the CPU as a Wishbone slave at
  `0x30000000`.
- Firmware talks to the USB controller through HPI-style data, mailbox, address,
  and status registers.

## What Is Working

- VGA timing and signal routing are reported working in `HANDOFF.md`.
- The code in `de2_115_vga_target.py` contains a simple 640x480 generator using
  a dedicated VGA clock domain and direct sync/data generation.
- The firmware initializes the LCD, drives LEDs and hex displays, and can read
  and write controller registers through the bridge.
- The handoff notes that controller identity register values match the Cypress
  CY7C67200 defaults.

## Main Blocker

The current firmware attempts a high-level USB host initialization sequence too
early. The root handoff documents that the CY7C67200 needs its proprietary LCP
firmware loaded into internal RAM first. Until that happens, the code in
`firmware/src/main.c` stalls waiting for `COMM_ACK` after issuing
`HUSB_SIE1_INIT_INT`.

## Naming Mismatch To Be Aware Of

`isp1761.py` is named and commented as though it targets an NXP ISP1761, but the
active project understanding is that the hardware is actually a Cypress
CY7C67200. The module currently behaves as a generic external bus bridge, so the
name is misleading but not functionally decisive.

## Reference Material Versus Active Source

The repository mixes active source with large volumes of reference material:

- `DE2_115_demonstrations/` contains Terasic example designs and likely the LCP
  blob source needed for the next USB step.
- `Downloads/` contains manuals, vendor tools, and extracted System Builder
  artifacts used to reconstruct accurate board mappings.
- `build/` contains generated LiteX outputs and Quartus products, not hand-edited
  source.
- The many `.jpg`, `.mp4`, and `.srt` files are evidence and observation
  artifacts from bring-up, not implementation code.

## Practical Next Step

The next implementation step should be:

1. Extract the LCP array from the Terasic demo header referenced in `HANDOFF.md`.
2. Add an HPI memory loader in `firmware/src/main.c`.
3. Boot the LCP firmware on the CY7C67200.
4. Retry the existing initialization and endpoint polling flow.
