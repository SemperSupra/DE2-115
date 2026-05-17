# Handoff Report: 2026-05-17 (Board-A HPI Confirmation)

## Current Status
- **Board Life:** **RESTORED on board A with candidate pad-capture image**. Board
  B was swapped out, board A was swapped in, and board A is programmed with
  checksum `0x033626D0` and pings at `192.168.178.50`.
- **Candidate image:** `artifacts\de2_115_vga_platform_hpi_pad_capture_033626D0_20260517.sof`.
- **Etherbone:** **FUNCTIONAL on candidate image**.
  `scripts\ethernet_low_speed_test.py --ping-count 20 --csr-loops 128 --bind-port 1235`
  passed on board A and read identifier prefix `LiteX VGA Test SoC on DE`.
- **UART:** **FUNCTIONAL**. BIOS heartbeat logs are visible on COM3 at 115200 baud.
- **USB HPI Debug:** **Rung 1 still failed**.
    - Fast canonical probe (`ACCESS_CYCLES=6`) returns all `0x0000`.
    - Fast index-15 / `legacy-data2-addr3` probe returns stable `0xf2f2`,
      not the written RAM words, so it is alias evidence rather than a pass.
    - HPI0 source/probe canonical read capture confirms the bridge asserts a
      real read cycle (`addr=0`, `CS_N=0`, `RD_N=0`, `RST_N=1`) with fast
      timing, while sampled HPI data remains `0x0000`.
    - On-FPGA pad snapshot confirms canonical data write drives
      `hpi_data=0x55aa` at `addr=0`, but canonical data read samples
      `hpi_data=0x0000` at `addr=0` with `CS_N=0`, `RD_N=0`, `WR_N=1`.
    - Board A reproduced the same canonical pad snapshot as board B:
      write data is visible at the FPGA pad-facing bus, while read data remains
      `0x0000`. The legacy/index-15 alias changed to `0xcfcf`, confirming it is
      not valid memory readback.

## Key Changes
- **ROM Size:** Permanently increased to 64 KiB (`0x10000`) to fit BIOS + firmware.
- **CSR Map:** Aligned firmware with the shifted CSR map.
- **Ethernet Pin Note:** Pin audit shows `ENET1_GTX_CLK` is `PIN_C23` and
  `PIN_C22` is `ENET1_TX_CLK`; do not apply the older C22 note blindly.
- **HPI Fix:** Re-applied 2-cycle address setup phase in the bridge.
- **HPI Pad Capture:** Added on-FPGA 64-bit pad snapshots for canonical address
  write, data write, and data read.
- **CI Delegation:** Added manual workflow dispatch and fixed stale CI gates.
  Static Checks and LiteX SoC Build both pass under manual dispatch.

## Next Steps for Codex CLI
1.  **Review Jules feedback:** Jules session `14997796971249417694` is reviewing
    the narrow pad-capture implementation and was still running at handoff.
2.  **Terasic demo or protocol review:** Second-board confirmation is complete:
    board A matches board B at the canonical readback failure. The next useful
    boundary is comparing against a known-good Terasic CY7C67200 USB demo
    bitstream or auditing the HPI reset/strap/protocol assumptions.
3.  **Do not run LCP:** Rung 1 canonical memory write/read is not proven.
4.  **Board swaps:** Four DE2-115 boards are available. Swap only after the
    same candidate SOF has a clear pass/fail on the first board.

## Environment
- **Branch:** `ethernet-baseline-shim`
- **Live image on board A:** `artifacts\de2_115_vga_platform_hpi_pad_capture_033626D0_20260517.sof`
- **Port:** `litex_server` target UDP 1234; host bind port 1235 for tests.
- **UART:** COM3, 115200.
- **Latest commits:** `f21b996` adds pad snapshots/orchestration; `359c92e`
  enables manual CI dispatch; final handoff updates are on this branch.
