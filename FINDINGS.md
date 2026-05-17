# Findings - May 17, 2026

## Milestone: Local Build Baseline Verified
Successfully achieved local build parity with the known-good validation image. The environment is now capable of producing booting bitstreams with working networking and UART.

## 1. The "Empty ROM" Diagnosis
- **Symptom:** Board dead, no ping, no UART.
- **Cause:** Increasing ROM size to 64KiB shifted the CSR map, making old firmware hang. Reverting to 32KiB caused a silent BIOS overflow during build, resulting in an empty ROM.
- **Fix:** Locked ROM at 64KiB, rebuilt firmware against new headers, and ensured `.init` files are correctly located by Quartus.

## 2. Ethernet Pin Contention
- **Symptom:** Networking died after UART pin correction.
- **Cause:** Typo in `surgical_pins.tcl` assigned `eth_gtx_clocks1_tx` to `C23` instead of `C22`.
- **Fix:** Corrected pin assignment in both TCL and QSF.

## 3. HPI Status (Blocker)
- **Status:** **0x0000 Readback**.
- **Evidence:** `trigger_hpi.py` and `cy_hpi_ladder_probe.py` consistently return zeros.
- **Current Logic:** Includes 2-cycle address setup phase.
- **Jules Insight:** Historical success was achieved with "Index 15" mapping and "Fast Timing" (6 cycles). This is the primary path forward.
