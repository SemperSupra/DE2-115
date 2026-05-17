# Handoff Report: 2026-05-17 (Post-Baseline Restoration)

## Current Status
- **Board Life:** **RESTORED**. The board pings at `192.168.178.50` and boots to the BIOS.
- **Etherbone:** **FUNCTIONAL**. Identifier "LiteX VGA Test S" can be read over the network.
- **UART:** **FUNCTIONAL**. BIOS heartbeat logs are visible on COM3 at 115200 baud.
- **USB HPI Debug:** **REPRODUCED BLOCKER**. 
    - Readback still returns `0x0000` (`hpi=0000` in logs).
    - Ladder probe across all mappings/timings returned zeros.
    - **Hypothesis:** The physical pins are working (bridge is active), but the timing or logic is still not satisfying the CY7C67200 requirements.

## Key Changes
- **ROM Size:** Permanently increased to 64 KiB (`0x10000`) to fit BIOS + firmware.
- **CSR Map:** Aligned firmware with the shifted CSR map.
- **Ethernet Fix:** Corrected `eth_gtx_clocks1_tx` to `PIN_C22`.
- **HPI Fix:** Re-applied 2-cycle address setup phase in the bridge.

## Next Steps for Codex CLI
1.  **Fast Timing:** Apply Jules' recommendation of `ACCESS_CYCLES=6`.
2.  **Index 15 Mapping:** Test the Jules-discovered mapping: `DATA=A2, MAILBOX=A1, ADDR=A3, STATUS=A0`.
3.  **SignalTap Capture:** Use the restored environment to capture the setup phase on physical pins.

## Environment
- **Branch:** `ethernet-baseline-shim`
- **Port:** `litex_server` on 1234.
- **UART:** COM3, 115200.
