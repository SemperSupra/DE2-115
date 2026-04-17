# Project Map

## Top-Level View

### Active Source

- `de2_115_vga_platform.py`
  - Purpose: LiteX platform with pin assignments for VGA, Ethernet, LCD, and USB.
  - **Correction:** Uses on-board PHY pins (`B21`, `C20`, `C19`).
- `de2_115_vga_target.py`
  - Purpose: SoC target definition (VexRiscv, SDRAM, Peripherals).
  - **USB:** Drives DACK/DREQ strapping pins for HPI mode.
- `rtl/cy7c67200_wb_bridge.v`
  - Purpose: Wishbone-to-HPI bridge logic.
  - **Debug:** Includes a 160-bit ISSP diagnostic probe.
- `firmware/src/main.c`
  - Purpose: SoC bring-up firmware.
  - **Features:** MDIO scanner, PHY HW reset, HPI strapping diagnostic.
- `firmware/src/lcp_blob.h`
  - Purpose: Extracted CY7C67200 LCP (BIOS) firmware blob.

### Scripts & Debug Tools

- `observe_vga.py` / `read_vga.py`
  - VGA console capture and OCR-based text extraction.
- `scripts/read_captured_hpi.tcl` / `decode_probe.py`
  - JTAG-based HPI bus tracing and signal decoding.
- `analyze_leds.py`
  - OpenCV-based LED spot detection from board photos.

## Directory Structure

- `rtl/`: Custom Verilog modules (HPI bridge, VGA text console).
- `firmware/src/`: C source for the RISC-V SoC.
- `scripts/`: Build and programming automation.
- `tools/`: External SDKs (Epiphan KVM, AgentWebCam).
- `local_artifacts/`: Captured logs and screenshots (untracked).

## Development Workflow

1.  **Modify Firmware:** Edit `firmware/src/main.c`.
2.  **Update Gateware:** Run `scripts/build_soc.sh` inside Docker.
3.  **Quartus Compile:** Run `quartus_sh --flow compile` in the gateware directory.
4.  **Program:** Use `load_bitstream.ps1`.
5.  **Debug:** Use `read_captured_hpi.tcl` for bus traces or `read_vga.py` for OCR logs.
