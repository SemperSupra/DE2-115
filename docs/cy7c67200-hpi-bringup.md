# CY7C67200 HPI Bring-up Path

This document outlines the architecture, memory mapping, known issues, and validation plan for the CY7C67200 USB Host Port Interface (HPI) integration into the LiteX/VexRiscv SoC on the DE2-115 platform.

## Current Architecture

The DE2-115 provides a Cypress CY7C67200 USB OTG controller. The integration uses a Wishbone-to-HPI bridge rather than the standard Qsys/Avalon approach provided in Terasic reference designs:

1.  **LiteX SoC (Wishbone):**
    *   The SoC maps the CY7C67200 USB controller to a Wishbone slave interface region at `0x82000000` (via `de2_115_vga_target.py` and `USB_OTG_BASE`).
    *   Unlike the Qsys/Avalon architecture where Avalon signals map somewhat directly to HPI, this design uses `cy7c67200_wb_bridge.v` to convert 32-bit Wishbone transactions to 16-bit HPI transactions.
2.  **HPI Bridge (`cy7c67200_wb_bridge.v`):**
    *   Maintains an internal state machine (IDLE -> WAIT -> ACK -> TURNAROUND) to satisfy the timing requirements of the CY7C67200.
    *   Supports runtime-configurable timing (access cycles, turnaround cycles) via debug register mapping.
3.  **Terasic Shim (`CY7C67200_IF.v`):**
    *   The bridge interfaces with the physical HPI pins through a legacy Terasic shim.

## Known Risks and Timing Implications

*   **Setup Time Violation Risk:** The CY7C67200 hardware manual requires at least 1 cycle of setup time for address and chip-select signals before asserting read/write strobes to prevent internal address aliasing.
    *   *Current State:* The `CY7C67200_IF.v` shim registers the incoming Wishbone signals but asserts `HPI_ADDR`, `HPI_CS_N`, `HPI_RD_N`, and `HPI_WR_N` concurrently on the output pins.
    *   *Recommendation:* This is documented in the RTL. If instability is observed during read/write cycles, the bridge should be modified to assert `HPI_ADDR` and `HPI_CS_N` one clock cycle before `HPI_RD_N`/`HPI_WR_N`.
*   **16-bit vs 32-bit:** The HPI interface is fundamentally 16-bit, but the Wishbone bus is 32-bit. The bridge places 16-bit read data in the lower half of the 32-bit word. Firmware must ensure it reads/writes appropriately to avoid endianness or byte-enable issues.
*   **JTAG Bone:** JTAGBone is disabled in LiteX to prevent conflicts with Altera debugging tools (SignalTap). Debugging the HPI bus should rely on the internal `LiteScopeAnalyzer` instances rather than external JTAG injection.

## Staged Validation Plan

The firmware (`cy7c67200_bringup.c`) implements a multi-stage validation sequence to bring up and verify the HPI link:

1.  **Raw HPI Reset/Control Register Access:** Validate that the LiteX CPU can read and write the debug timing registers inside the `cy7c67200_wb_bridge.v` without hanging the Wishbone bus.
2.  **Device Reset:** Assert and de-assert `HPI_RST_N`, then transition to optimized timing (10 cycles access, 2 cycles turnaround).
3.  **Known CY7C67200 Register Readback:** Attempt to read basic registers (e.g., `CY_HW_REV_REG`) to confirm the device is responding and the data bus is not floating.
4.  **Internal RAM Read/Write Probe:** Write a known value to the CY7C67200 internal RAM (e.g., `0x1000`) and read it back to verify bidirectional data integrity.
5.  **Mailbox/Status Polling:** Write to the Mailbox register and poll the Status register to verify the LCP (Local CPU) inside the CY7C67200 is communicating.
6.  **SIE Message Detection:** Wait for the Host SIE to initialize and generate EOP/SOF interrupts via the HPI interrupt pins/status registers.
7.  **USB Keyboard Enumeration:** Once basic SIE messages are confirmed, proceed with scanning and minimal HID polling (handled by external modular tests).
