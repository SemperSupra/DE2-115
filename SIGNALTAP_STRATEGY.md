# SignalTap Debugging Strategy for DE2-115 Bring-Up

This document outlines a strategy for utilizing Intel's SignalTap II Logic Analyzer effectively within the DE2-115 FPGA board bring-up project. The project currently integrates a LiteX SoC, VexRiscv CPU, baremetal firmware, and various custom peripherals (VGA, USB HPI bridge).

## Current State of Debugging

The current debugging infrastructure heavily relies on:
1. **LiteScope:** Used for capturing Wishbone/HPI signals (`hpi_analyzer` in `de2_115_vga_target.py`).
2. **In-System Sources and Probes (ISSP):** Used for real-time interaction (e.g., reset, basic captures) with the HPI bridge via TCL scripts.
3. **JTAG Constraints:** JTAGBone has been removed from the LiteX SoC design to avoid multiplexing conflicts with ISSP and potential SignalTap usage.
4. **Host/Container Separation:** Quartus (and thus SignalTap) is installed natively on the host development machine with direct USB access to the USB Blaster. The LiteX tools run inside a Docker container without direct JTAG access, presenting a logistical hurdle for native LiteX debugging.

While LiteScope is powerful for in-system Wishbone analysis, SignalTap II offers deeper integration into Quartus, precise trigger conditions, and better visibility into lower-level hardware signaling independent of the LiteX infrastructure. Furthermore, because Quartus runs directly on the host, SignalTap currently provides the most reliable access to the JTAG chain without requiring complex container USB passthrough configurations.

## Evidence-Based Strategy

Based on industry best practices for FPGA board bring-up, debugging should be tiered, non-intrusive, and resource-aware.

### 0. Environment Reality Check (Host vs. Container)
**Problem:** The LiteX build environment is containerized and currently lacks direct USB passthrough to the DE2-115's USB Blaster, whereas the host OS has direct access to the JTAG interface via native Quartus.
**Recommendation:**
* In the short term, exclusively rely on native host tools (SignalTap, ISSP) for hardware verification to bypass container networking/USB complexities.
* In the medium term (once lower-level hardware and timing issues are resolved and the focus shifts to firmware), prioritize configuring the Docker environment (e.g., via `--device=/dev/bus/usb` on Linux or specialized remote JTAG servers) to allow seamless LiteScope/litex_server debugging.

### 1. Unified JTAG Hub Management
**Problem:** The DE2-115 has a single physical JTAG chain. Multiple debug tools (LiteScope, JTAGBone, ISSP, SignalTap) competing for the JTAG hub can cause instability and routing failures.
**Recommendation:**
* Exclusively use Quartus-native tools (SignalTap, ISSP) for lower-level hardware debugging until the physical interfaces are proven.
* Once stable, transition to LiteScope for higher-level system/software debugging.
* Do not attempt to run SignalTap and LiteScope simultaneously unless absolutely necessary and thoroughly verified.

### 2. Clock Domain Crossing (CDC) Visibility
**Problem:** The design uses multiple clock domains (`sys`, `sys_ps`, `vga` at 25MHz, `eth` at 125MHz). Debugging signals across these domains without proper synchronization leads to metastable captures and false conclusions.
**Recommendation:**
* Instantiate separate SignalTap instances for distinct clock domains.
* For the VGA domain, use the 25MHz VGA clock as the acquisition clock.
* For the Ethernet (RGMII) domain, use the 125MHz Ethernet clock.
* For the HPI/USB domain, use the main system clock (`sys`).

### 3. Modular "Plug-and-Play" Debugging (STP Files)
**Problem:** Compiling SignalTap instances directly into the RTL (using `(* noprune *)` or explicit instantiation) clutters the source code and requires full recompilations to change triggers.
**Recommendation:**
* Use `.stp` (SignalTap Configuration) files managed outside the RTL.
* Maintain separate `.stp` files for different subsystems: `usb_hpi_debug.stp`, `eth_rgmii_debug.stp`, `vga_debug.stp`.
* Use the Quartus Rapid Recompile feature when modifying trigger conditions within an existing `.stp` file to save build time.

## Device-Specific Implementation Plans

### A. USB HPI Bridge (CY7C67200)
**Current Challenge:** The CY7C67200 chip is silent, and timing sweeps are required to wake it up.
**SignalTap Strategy:**
* **Signals to Tap:** `hpi_cs_n`, `hpi_rd_n`, `hpi_wr_n`, `hpi_addr`, `hpi_data[15:0]`, `hpi_rst_n`, and the internal state machine variables (`state`, `count`).
* **Trigger Condition:** Trigger on the falling edge of `hpi_cs_n` (start of transaction) or the transition out of the `STATE_IDLE` state.
* **Goal:** Verify that the setup, pulse width, and hold times of the read/write strobes match the Cypress datasheet requirements precisely.

### B. Ethernet RGMII (Marvell 88E1111)
**Current Challenge:** MDIO management is working, physical link is UP, but PHY registers report LINK DOWN to the MAC.
**SignalTap Strategy:**
* **Signals to Tap:** `rx_ctl`, `rx_data[3:0]`, `tx_ctl`, `tx_data[3:0]`, and the 125MHz Ethernet clocks.
* **Trigger Condition:** Trigger on `rx_ctl` asserting (indicating valid incoming data or control frames) or on specific MDIO register write completion flags.
* **Goal:** Inspect the raw RGMII traffic to see if in-band status (if enabled) or auto-negotiation pulses are actually reaching the FPGA pins despite the PHY register state.

### C. VGA Test Pattern Generator
**Current Challenge:** Working, but isolated from the VexRiscv CPU framebuffers.
**SignalTap Strategy:**
* **Signals to Tap:** `h_cnt`, `v_cnt`, `hsync_n`, `vsync_n`, `blank_n`, and the RGB output registers.
* **Trigger Condition:** Trigger on the transition of `vsync_n` to capture an entire frame's worth of synchronization boundaries, or trigger on specific `h_cnt`/`v_cnt` coordinate matches to debug pixel-level glitches.
* **Goal:** Ensure accurate sync pulse widths and porch timings according to the VESA 640x480 standard.

## Firmware and Driver Co-Development

SignalTap provides the hardware truth, but effective drivers require software context.

1. **Hardware-Triggered Software Breakpoints:** Expose a dedicated GPIO pin connected to the VexRiscv. The firmware can toggle this pin when a specific driver function (e.g., `husb_init()`) is called. SignalTap can trigger on this pin's edge, aligning the hardware capture perfectly with the software execution state.
2. **Software-Triggered Hardware State:** Conversely, use ISSP or memory-mapped control registers to inject a trigger signal from hardware into the LiteX interrupt controller, pausing the VexRiscv when a specific hardware anomaly (e.g., HPI timeout) occurs.

## Summary

Adopting isolated `.stp` files tailored to specific clock domains, prioritizing native Quartus tools during low-level bring-up, and utilizing cross-triggering between hardware events and software execution will provide the highest fidelity insights for the remaining DE2-115 peripheral integration.