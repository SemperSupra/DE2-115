# HPI Breakthrough Investigation Report
Date: 2026-05-10

> 2026-05-11 update: the "Index 15" swapped mapping below is no longer the
> accepted target map. Primary references and Terasic/Linux examples agree on
> the canonical map `DATA=0`, `MAILBOX=1`, `ADDR=2`, `STATUS=3`. Treat the old
> swapped mapping as a negative-control observation until re-proven by
> `scripts/cy_hpi_ladder_probe.py`.

## 1. Summary of Findings
The investigation into the host-crash-interrupted Jules session has confirmed a successful breakthrough in the CY7C67200 HPI read/write path. The primary blockers were a combination of hardware-sensitive timing and incorrect pin mapping.

### Key Breakthrough Components:
1.  **RTL Strobe Pulsing ("The Pulse Fix"):**
    - **Location:** `rtl/cy7c67200_wb_bridge.v`
    - **Mechanism:** The `RD_N` and `WR_N` signals are now generated as pulses *inside* the `CS_N` assertion window.
    - **Why it worked:** The CY7C67200 requires stable address and Chip Select signals before the Read/Write strobes transition. The previous "level-triggered" approach caused simultaneous transitions that the chip's internal state machine likely ignored or errored on.

2.  **Timing Sensitivity:**
    - **Result:** Success was achieved with "fast" timing (`ACCESS_CYCLES=3` to `6`).
    - **Finding:** The chip appears more responsive to tighter bus cycles. Slow cycles (the default 63) often returned `0x0000`.

3.  **Interrupt Mapping Correction:**
    - **Location:** `de2_115_vga_platform.py`
    - **Change:** Mapped `int0` to `PIN_D5` (the documented `OTG_INT`) and `int1` to `PIN_E5`. Previous configurations were attempting to use `E5` (labeled `TD_HS`) as the primary interrupt, which caused no-response states.

4.  **Register Mapping Clue:**
    - **Result:** Address permutation index 15 (`data=A2, mailbox=A1, address=A3, status=A0`) produced the first reliable non-zero data.
    - **Implication:** The physical address lines `OTG_ADDR[1:0]` on the DE2-115 may be logically swapped or mapped non-linearly in the current bridge.

## 2. Verified Success State
- **Mailbox Write:** Proven at pins (`0xfa50` captured via HPI0 probe).
- **HPI Readback:** Successfully retrieved `readback=0x1000` and `mailbox=0x00df`.
- **Status:** The chip is alive and responding to the host.

## 3. Current Constraints
- **Ethernet Regression:** The most recent automated builds (checksum `0x032C9C4C`) show Ethernet reachability issues.
- **Baseline:** `validation_images/de2_115_vga_platform_eth10_switchfix_validated_20260427.sof` remains the known-good network baseline.
