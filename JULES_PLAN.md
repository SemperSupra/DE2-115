# JULES_PLAN.md - DE2-115 SoC Evolution Strategy

## 1. Vision
Transform the DE2-115 LiteX SoC from a "bring-up" prototype into a verified, high-performance networking and USB-OTG host platform. This requires moving from manual diagnostic scripts to automated, self-verifying build pipelines.

## 2. Priority Phase 1: Infrastructure & Reliability
### **A. Path Sanitization (Anti-Regression)**
*   **The Problem:** Docker-generated `.qsf` files contain absolute Linux paths (e.g., `/pythondata-cpu-vexriscv/...`) which cause Quartus on Windows to silently drop the CPU.
*   **Action:** Implement a pre-synthesis hook in Python (within `de2_115_vga_target.py`) that scans the generated `.qsf` and warns/errors if any absolute Linux paths are detected.
*   **Goal:** Zero "black box" CPU failures.

### **B. Automated HIL (Hardware-In-the-Loop) Testing**
*   **The Problem:** Remote debugging relies on manual interpretation of screenshots.
*   **Action:** Create a `verify_boot.py` script that:
    1.  Programs the FPGA.
    2.  Captures the VGA screen via `AgentKVM2USB`.
    3.  Uses simple OCR or template matching to find the "DE2-115 DEEP DIVE" string.
    4.  Fails the CI/CD pipeline if the screen is blank or garbage.

## 3. Priority Phase 2: Ethernet RGMII Performance
### **A. Clock Mapping Alignment**
*   **Investigation:** The Marvell 88E1111 requires `GTX_CLK` (Pin A14) for 1000Mbps mode. Current mapping uses `TX_CLK` (B17), which is for 10/100 mode.
*   **Action:** Update `de2_115_vga_platform.py` to correctly map the `rgmii_eth` clocks to Pin A14.
*   **Verification:** Confirm "LINK UP 1000M" on the VGA console.

### **B. Network Stack Integration**
*   **Action:** Integrate the LiteX `BIOS` networking commands (`ping`, `netboot`) and verify `litex_server` reachability over UDP.

## 4. Priority Phase 3: USB Host Controller (CY7C67200)
### **A. LCP Firmware Port**
*   **Context:** The chip requires a binary blob (LCP) to be loaded via HPI to act as a USB host.
*   **Action:** Port the Terasic `pcd_asm.h` loading logic into a clean C driver in `firmware/src/usb_host.c`.
*   **Goal:** Enumerate a simple USB HID device (keyboard/mouse) and display its VID/PID on the VGA console.

## 5. Success Metrics for Jules
1.  **Green CI:** `run.bat` completes and `verify_boot.py` passes.
2.  **Pingable:** `ping 192.168.178.50` responds from the board.
3.  **USB Visible:** VGA console shows "USB Device Detected: [VID:PID]".

---
*Created by Gemini CLI - 2026-04-19*
