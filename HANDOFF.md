# Handoff Report: 2026-05-16 (Pre-Reboot)

## Current Status
- **USB HPI Debug:** **DIAGNOSED AS LOGICAL**. 
    - Board swap confirmed the issue is NOT a physical failure on Board A's Pin H7.
    - Failure is a timing/race condition on the asynchronous HPI bus.
- **RTL Refactor:** **IMPLEMENTED**. 
    - `cy7c67200_wb_bridge.v`: Added `STATE_SETUP` for 2-cycle address setup.
    - `CY7C67200_IF.v`: Added explicit 4-cycle tri-state at the start of read cycles.
- **7-Segment Display:** **FIXED**. Inverted segment logic in `de2_115_vga_target.py` for active-low hardware.
- **Blocked On:** SoC regeneration (Docker error) and full build.

## Summary of Changes
- **Logical Fixes:** HPI timing refactor and 7-segment polarity inversion applied to local source.
- **Pins:** Reverted to standard `H7` mapping (no jumpers needed).
- **Documentation:** Updated `FINDINGS.md` and `ORCHESTRATION_PLAN.md` with the logical pivot.

## Next Steps (Post-Reboot)
1.  **Regenerate SoC:** Run `./scripts/build_soc.sh 1` (requires Docker).
2.  **Apply Pins:** Run `quartus_sh -t surgical_pins.tcl`.
3.  **Full Build:** Run clean Quartus compile in `build/terasic_de2_115/gateware`.
4.  **Verification:** Load SOF and run `scripts/trigger_hpi.py`. Target is `0x0011`.

## Repositories
- **Branch:** `ethernet-baseline-shim`
- **Status:** Committing and pushing logical fixes now.
