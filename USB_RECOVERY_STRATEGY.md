# USB HPI Recovery Strategy - DE2-115

## 1. Problem Statement
The CY7C67200 (USB Controller) Host Port Interface (HPI) is currently unresponsive. All reads from the internal memory or registers return `0x0000`. The LiteX Wishbone-to-HPI bridge appears to stall in `STATE_WAIT`, suggesting that the CY7C67200 is not driving the data bus or the timing is so slow (1.26us pulses) that the chip's internal state machine is timing out.

## 2. Root Cause Hypothesis
*   **Excessive Pulse Width:** The current 63-cycle (`0x3F`) access period is too slow for the CY7C67200.
*   **Reset State:** The chip might be stuck in a boot loop or a stand-alone mode (GPIO30/31 straps) because the initial reset was too short or missing.
*   **Bus Contention:** Undriven sideband pins (DACK/DREQ) might be floating into an active state.

## 3. Recovery Plan

### Phase 1: Timing & Reset Validation
1.  **Reduce Access Cycles:** Lower `cfg_access_cycles` from 63 to 10 (200ns @ 50MHz). This aligns with standard SRAM timings.
2.  **Explicit HW Reset:** Hold `OTG_RST_N` low for 500ms, then high for 500ms before any access.
3.  **Hardware Loopback Test:** Attempt to write `0x1234` to `HPI_ADDRESS` (Offset 2) and read it back. Since this register is a simple hardware latch inside the CY7C67200, it should work even if the internal BIOS/CPU is not running.

### Phase 2: LCP (Link Control Protocol) Handshake
1.  **Command Reset:** Write `COMM_RESET` (`0xFA50`) to the `MAILBOX` register.
2.  **ACK Polling:** Monitor `HPI_STATUS` bit 0. It should assert when the CY7C67200 BIOS has processed the command.
3.  **Read ACK:** Read the `MAILBOX` register to confirm the value is `COMM_ACK` (`0x0FED`).

### Phase 3: Firmware Injection
1.  Load the LCP jump-table and base BIOS code into the CY7C67200 internal RAM via HPI Data port.
2.  Jump to the entry point using the `COMM_JUMP2CODE` command.
3.  Initialize the USB Host stack (SIE1).
