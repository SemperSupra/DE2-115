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

## 4. 2026-05-17 Fast/Index-15 Ladder Continuation
- **Baseline restored:** The current build SOF (`0x033B0F01`) programmed but did
  not ping. The validated Ethernet image
  `validation_images/de2_115_vga_platform_eth10_switchfix_validated_20260427.sof`
  was restored and passed `10/10` ping plus `64` Etherbone CSR loops.
- **Fast canonical result:** `scripts/cy_hpi_ladder_probe.py --maps canonical --timings fast`
  still failed Rung 1. Canonical block and separated-address reads were all
  `0x0000`.
- **Fast index-15 result:** `legacy-data2-addr3` (`DATA=A2`, `MAILBOX=A1`,
  `ADDR=A3`, `STATUS=A0`) returned stable `0xf2f2`, not the expected RAM words.
  Treat this as alias/nonzero evidence, not a ladder pass.
- **HPI0 read evidence:** Source/probe captured a canonical data read with
  `addr=0`, `CS_N=0`, `RD_N=0`, `WR_N=1`, `RST_N=1`, `ACCESS_CYCLES=6`,
  `SAMPLE_OFFSET=2`, `TURNAROUND=2`, and sampled `hpi_data=0x0000`.
- **HPI0 alias evidence:** Source/probe captured an index-15/status read at
  `addr=3` with the same active read controls and `hpi_data=0xf2f2`.
- **Conclusion:** The FPGA bridge is issuing active HPI read cycles. The next
  unknown is the external CY7C67200 pad-level behavior or a remaining protocol
  assumption, not whether the Wishbone bridge attempts a read.

## 5. 2026-05-17 No-External-Analyzer Capture Plan
- **Constraint:** No external logic analyzer is available for the HPI pins.
- **Approach:** Add on-FPGA 64-bit pad snapshots to `cy7c67200_wb_bridge.v` and
  expose them through the existing USB debug window at `0x82000110` through
  `0x82000124`.
- **Host tool:** `scripts/hpi_pad_capture_debug.py` now supports explicit HPI
  maps and timing profiles. Canonical fast is the acceptance path.
- **Delegation:** Jules review session `14997796971249417694` was created for
  isolated review of the pad-capture RTL/script. GitHub Actions can validate
  software syntax and Docker SoC generation after commit/push. Quartus compile,
  programming, Ethernet gate, pad snapshot, and board swaps remain local-only.

## 6. 2026-05-17 HPI Pad Snapshot Result
- **Candidate image:** `artifacts/de2_115_vga_platform_hpi_pad_capture_033626D0_20260517.sof`.
- **Build evidence:** SoC generation passed; Quartus full compile passed with
  checksum `0x033626D0`, 0 errors, and timing met despite existing
  unconstrained-clock warnings.
- **Ethernet gate:** Candidate image passed `20/20` ping and `128` Etherbone
  CSR loops before HPI capture.
- **Canonical fast pad capture:** `scripts/hpi_pad_capture_debug.py --start-server --bind-port 1235 --experimental-rtl --map canonical --timing fast --address 0x1000 --value 0x55aa`
  produced:
  - Address write: `addr=2`, `CS_N=0`, `WR_N=0`, `RD_N=1`.
  - Data write: `addr=0`, `CS_N=0`, `WR_N=0`, `RD_N=1`, `hpi_data=0x55aa`.
  - Data read: `addr=0`, `CS_N=0`, `RD_N=0`, `WR_N=1`, `hpi_data=0x0000`.
- **Interpretation:** The FPGA is driving canonical writes correctly at the
  pad-facing bus and is issuing a valid canonical read strobe. The CY7C67200 is
  still not driving nonzero data back to the FPGA input buffers for canonical
  memory readback.
- **Follow-up ladder:** The same candidate image still failed canonical Rung 1.
  The legacy/index-15 map returned a stable nonzero alias (`0xbfbf` in this
  placement), not the expected RAM words.
- **Next boundary:** Second-board confirmation is now complete in Section 8.
  Continue as a design/protocol/reset/strap issue and compare against a known
  Terasic USB demo before any LCP work.

## 7. 2026-05-17 Delegation Results
- **Google Jules:** Review session `14997796971249417694` was opened for the
  narrow pad-capture RTL/script review. It was still running at handoff time.
- **GitHub Actions:** Static Checks and LiteX SoC Build both pass after fixing
  the stale orchestration grep, adding manual dispatch, and fixing the HPI
  simulation command to compile `tb.v` instead of `test_hpi_sim.py`.
- **Local-only hardware:** Quartus compile, programming, Ethernet gate, HPI pad
  snapshot, and ladder probe completed locally because they require Quartus
  and/or physical DE2-115 hardware.

## 8. 2026-05-17 Board-A Swap Result
- **Action:** Board B was swapped out and board A was swapped in. The same
  candidate SOF, `artifacts/de2_115_vga_platform_hpi_pad_capture_033626D0_20260517.sof`,
  was programmed directly over USB-Blaster.
- **Programming evidence:** Quartus programmer accepted the image for
  `EP4CE115F29@1` with checksum `0x033626D0`.
- **Ethernet gate:** Board A passed
  `python scripts/ethernet_low_speed_test.py --ping-count 20 --csr-loops 128 --bind-port 1235`.
  Ping had one initial timeout (`19/20` replies), but Etherbone CSR stress passed
  all `128` loops and the script reported `ETHERNET_LOW_SPEED_TEST_PASS`.
- **Canonical fast pad capture:** Board A matched board B. Address write and
  data write are visible at the FPGA pad-facing bus, including
  `hpi_data=0x55aa` for the data write. Canonical read still samples
  `hpi_data=0x0000` with `CS_N=0`, `RD_N=0`, `WR_N=1`.
- **Follow-up ladder:** Board A still failed canonical Rung 1. The
  `legacy-data2-addr3` map returned stable `0xcfcf`, which differs from the
  earlier board-B alias but still does not match expected RAM words.
- **Interpretation:** The same failure on two boards argues against a single
  damaged CY7C67200 or board assembly issue. Treat the next boundary as a
  design/protocol/reset/strap comparison against the Terasic USB demo, not as
  more LCP work.

## 9. 2026-05-17 Reset/Timing Sweep After Board-A Swap
- **Reset dwell sweep:** Board A was probed with reset held low for `0.5 s` and
  high for `2.0 s` before HPI access.
- **Timing sweep:** Canonical and `legacy-data2-addr3` maps were tested under
  `spec`, `fast`, and `slow` profiles. Canonical still returned all `0x0000`
  for memory, status, mailbox, CPU flags, HW revision, and power registers.
- **Legacy alias behavior:** The legacy map continued to return nonzero aliases,
  but the values varied by timing (`0xcfcf`, `0x1313`, `0x0101`, and one
  `0x0144` word under slow timing). This confirms the legacy path is not a
  valid memory/register readback path.
- **Pad snapshots under spec/slow:** Canonical writes still drove
  `hpi_data=0x55aa`. Canonical reads still sampled `hpi_data=0x0000` under
  both `spec` and `slow` timing.
- **Audit outcome:** No assigned pin or generated QSF entry drives CY DACK,
  GPIO30/GPIO31, VBUS-enable, or wake sideband nets. The current design leaves
  boot-selection sideband pins to board straps.
- **Next boundary:** Schematic/strap/VBUS audit and a Terasic demo rerun with
  explicit board-power/jumper observations. Do not run LCP/SIE/HID work.

## 10. 2026-05-17 Next-Phase Orchestration
- **Task relationship:** Board-swap confirmation and reset/timing sweeps are
  complete prerequisites. The active dependency chain is now: document current
  evidence, review schematic/strap/VBUS assumptions, rerun Terasic demo with
  explicit board observations, then decide whether canonical HPI Rung 1 can be
  resumed.
- **Parallel delegation:** Jules session `3912795874550261687` was opened to
  review the evidence and schematic/strap/VBUS plan. GitHub Actions remains
  responsible for repository static checks and LiteX SoC generation.
- **Sequential local gates:** Physical demo rerun, any board-power/VBUS/jumper
  observation, FPGA programming, Ethernet, and HPI capture are local-only.
- **Recommendation:** Do not change RTL again until the schematic/manual/demo
  comparison either identifies a concrete board-level requirement or clears
  the board-level configuration as a cause.
