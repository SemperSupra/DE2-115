# Findings

## Repository Purpose

This project is a DE2-115 FPGA board bring-up effort centered on a custom LiteX
SoC. It combines:

- LiteX + VexRiscv for the soft CPU and memory map.
- A custom VGA path that bypasses the heavy LiteX VGA framebuffers for a direct
  character-mode text console.
- A Wishbone-to-HPI bridge for the Cypress CY7C67200 USB controller.
- Remote observation tools using Epiphan KVM2USB and standard Webcams.

## Major Discoveries

### 1. Ethernet Pinout & MDIO Verification
- **Correction:** Default LiteX pins were for an extension card. Corrected `de2_115_vga_platform.py` to use on-board Marvell 88E1111 pins (`B21`, `C20`, `C19`).
- **Status:** MDIO management bus is 100% reliable. PHYs respond at addr 16 (Port 0) and 17 (Port 1).
- **Bit-Shift Resolved:** The consistent 1-bit shift in MDIO reads was fixed by adjusting the MDIO sampling point in the firmware (`mdio_read` now samples while MDC is HIGH). Manual shifts in firmware were removed.
- **In-Band Status:** Enabled RGMII in-band status in the PHY. The LiteEth core now correctly identifies the clock as **1000Mbps** (`INBAND: 00000004`).
- **The "Link Down" Mystery:** Physical LEDs (D1/1000 and D20/DUP) are solid green, and D19/RX is blinking, indicating a valid 1Gbps link. However, PHY Register 1 still reports **LINK DOWN**. This suggests an internal auto-negotiation or mode mismatch (e.g., Fiber vs. Copper) that prevents the PHY from asserting the link bit to the MAC.

### 2. USB (HPI) Bridge & Strapping
- **Bridge Fix:** Discovered and fixed a critical bug in `rtl/cy7c67200_wb_bridge.v`. The `debug_access` signal (used for runtime bridge configuration) had a faulty address decoder that ignored writes to `0x82000100`.
- **Strapping & Reset:** Verified that `OTG_RST_N`, `DACK#`, and `DREQ` are correctly managed for HPI mode strapping.
- **Status:** The bridge is now fully configurable at runtime (timing, reset toggle). The CY7C67200 chip remains silent, but we can now perform timing sweeps to wake it up.

### 3. Debugging Infrastructure
- **ISSP Capture:** Created `scripts/read_captured_hpi.tcl` to pull real-time bus traces via JTAG.
- **VGA OCR:** Created `read_vga.py` to automate log extraction from the video feed.

## Hardware Status

| Peripheral | Status | Notes |
| :--- | :--- | :--- |
| VexRiscv CPU | **Working** | Stable at 50MHz. |
| SDRAM | **Working** | 128MB accessible. |
| VGA Console | **Working** | 80x30 text mode, hardware font. |
| MDIO (Ethernet) | **Working** | 100% reliable register access. |
| Ethernet Data | **Blocked** | Link UP physically (LEDs), but DOWN in PHY registers. |
| HPI (USB) | **Blocked** | Bridge functional, timing sweep required. |

## Next Steps

1.  **Ethernet Force Mode:** Disable auto-negotiation and force the PHY to 1000Mbps Full-Duplex to see if the Link bit asserts.
2.  **USB Timing Sweep:** Use the runtime configuration registers to test different HPI `ACCESS_CYCLES` and `SAMPLE_OFFSET` values.
3.  **LCP Loading:** Once the chip responds, use the extracted `lcp_blob.h` to initialize the USB host.
