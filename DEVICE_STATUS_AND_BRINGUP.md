# USB Host Bring-Up Status (2026-05-05)

## Current Status
- USB Host port powered: Yes (4.99V)
- CY7C67200 HPI interface: Responding to read/write probes.
- Firmware bring-up: Initialized (with HPI loopback test bypassed).
- USB Packet status: Waiting for Beagle 12 verification with patched firmware.
- Ethernet gate for USB builds: Passing for the current root INT1-only bridge
  image, checksum `0x033328D9`. The gate now stresses `lcd_out` instead of
  red LEDs because USB diagnostic idle firmware owns `leds_r_out` as a
  heartbeat. Passive HPI debug-bit exposure in `last_ctrl` breaks the gate.
- USB interrupt pins are restored to the passing mapping: `int0=D5`,
  `int1=E5`.
- HPI writes are visible at the data path, but normal HPI reads remain
  `0x0000` across sample/access timing sweeps.
- `scripts\capture_hpi_source_probe.ps1` now provides a repeatable DATA-read
  capture. It shows reset released and `CS_N=0/RD_N=0/WR_N=1/ADDR=0`, while
  `hpi_data`, `cy_o_data`, and sampled read data are all `0x0000`.
- 2026-05-04 rerun on programmed checksum `0x033328D9` reconfirmed the same
  HPI boundary: write DATA shows `sample=0x1234/cy=0x1234`, normal DATA read
  returns `0x0000`, MAILBOX/STATUS read `0x0000`, and swapped A1/A0 read
  still returns the non-authoritative `0x0011` artifact.
- `scripts\hpi_cycle_loop.py` can now generate a repeatable analyzer-friendly
  HPI cycle stream without a new bitstream. Smoke command:
  `python scripts\hpi_cycle_loop.py --start-server --port 1235 --mode rw --count 3 --period-ms 50 --reset`
  repeated write/read cycles and reproduced `read=0x0000`.
- `scripts\run_hpi_external_capture_loop.ps1` wraps the cycle stream for
  capture use. It optionally runs a quick Ethernet gate, prints analyzer trigger
  guidance, writes `local_artifacts\hpi_external_analyzer_channels.csv`, starts
  the loop, and logs output under `local_artifacts`.
- 2026-05-05 live capture loop is running under
  `local_artifacts\hpi_external_capture_loop_live.log`; it has advanced past
  400k repeated cycles and still reports `read=0x0000`, `sample=0x0000`,
  `cy=0x0000`, `ctrl=0x03200800`. A simultaneous HPI0 source/probe snapshot
  saved in `local_artifacts\hpi_live_source_probe_capture.txt` captured
  `probe_data=48FC8FF7C9D6823B80000000000000000000000000000000`, decoded as
  `CS_N=0`, `RD_N=0`, `WR_N=1`, `ADDR=0`, reset released, and all data fields
  still `0x0000`.
- SignalTap diagnosis: QSF `USE_SIGNALTAP_FILE` is recognized by Quartus, but
  `.stp` auto insertion still emits a hub-only `.sld`. Explicit HDL
  `sld_signaltap` does instantiate and fit, but the tested images fail Ethernet
  bring-up, so the HDL analyzer is now guarded behind `HPI_PIN_SIGNALTAP` and
  should not be enabled in default root builds.
- No external logic analyzer is available. The replacement strategy is a
  weak-pullup diagnostic image: set `DE2_USB_HPI_WEAK_PULLUPS=1` during
  `scripts\build_soc.sh` to enable FPGA weak pull-ups only on
  `usb_otg_data[15:0]`, then run `scripts\run_hpi_weak_pullup_diag.ps1`.
  If reads become `0xffff` or mostly high, the CY is not driving DATA during
  reads; if they remain `0x0000`, the CY/board path is actively holding DATA
  low.
- 2026-05-05 weak-pullup diagnostic result: Quartus programmed checksum
  `0x03332BFF`; fitter confirms `Weak Pull Up = On` for all sixteen
  `usb_otg_data[*]` bidir pins. Ethernet gate passed with 49/50 ping and 512
  CSR loops. Eight HPI DATA write/read cycles still returned
  `read=0x0000`, `sample=0x0000`, `cy=0x0000`, `ctrl=0x03200800`, so the bus
  is not merely floating low with the FPGA input released.
- 2026-05-05 no-analyzer contrast run:
  `scripts\run_hpi_no_analyzer_contrast.ps1` passed a 20/20 ping plus 128 CSR
  Ethernet gate, then captured the weak-pullup split. Idle/released HPI0 showed
  `hpi_data=0xffff`, `cy_o_data=0xffff`, `sample_data=0xffff`; reset-low HPI0
  showed `hpi_rst_n=0`, `hpi_data=0xffff`, `sample_data=0xffff`; active DATA
  read showed `CS_N=0`, `RD_N=0`, `WR_N=1`, `ADDR=0`, `hpi_rst_n=1`, but
  `hpi_data=0x0000`, `cy_o_data=0x0000`, `sample_data=0x0000`. Sequential
  reads of DATA, MAILBOX, STATUS, and the non-authoritative ADDRESS port all
  returned `0x0000`. Log:
  `local_artifacts\hpi_no_analyzer_contrast.log`.
- 2026-05-05 reset timing sweep:
  `scripts\run_hpi_reset_timing_sweep.ps1` passed a 20/20 ping plus 128 CSR
  Ethernet gate, then tested 108 reset/timing combinations:
  reset-low `0.01/0.1/0.5/2.0s`, post-release wait `0.1/0.5/2.0s`,
  access cycles `10/32/63`, and sample offsets `2/8/16`. DATA, MAILBOX, and
  STATUS stayed `0x0000` before and after a DATA write in every row
  (`nonzero=0x0000`). Log: `local_artifacts\hpi_reset_timing_sweep.log`.
- 2026-05-05 local wiring fact check: `docs\CY7C67200_BOARD_WIRING_FACTS.md`
  records that the DE2 manual shows the CY7C67200 HPI interface and a `12MHz`
  `XTALIN` feed from MAX II `EPM240`. The BIOS manual says HPI co-processor
  boot requires `GPIO30=0/GPIO31=0`. Those boot pins are not exposed in the
  current platform, so `force_hpi_boot` is not a real strap override.
- 2026-05-05 mailbox sideband probe:
  `scripts\run_hpi_mailbox_sideband_probe.ps1` now arms HPI0 source/probe
  before issuing mailbox writes. Narrow rerun
  `local_artifacts\hpi_mailbox_sideband_probe_rerun4.log` captured an
  intentional `0xfa50` mailbox write with `captured=1`, `match=1`, `CS_N=0`,
  `WR_N=0`, `RD_N=1`, `ADDR=1`, reset released, and
  `write_data/sample_data/cy_o_data/hpi_data=0xfa50`. The subsequent STATUS
  and MAILBOX reads still returned `0x0000`, and idle sidebands stayed
  `INT0=1`, `INT1=1`, `DREQ=0`. This proves the FPGA write-window drive and
  HPI0 capture path are working, but it does not prove the CY BIOS is
  processing mailbox commands.
- 2026-05-05 reset-release sideband timeline:
  `scripts\run_hpi_reset_release_sideband_timeline.ps1` samples HPI0 idle
  sidebands after asserting and releasing CY reset. Rerun log
  `local_artifacts\hpi_reset_release_sideband_timeline.log` showed reset-low
  with `hpi_rst_n=0`, `INT0=0`, `INT1=1`, `DREQ=0`, and idle DATA high. After
  reset release, coarse samples at `0/100/500/1000/2000ms` all showed
  `hpi_rst_n=1`, `INT0=1`, `INT1=1`, `DREQ=0`, and idle DATA high. This proves
  the reset control has observable CY-side effect, but it did not reveal any
  sideband boot/mailbox activity after release.
- 2026-05-05 HPI address permutation sweep:
  `scripts\hpi_address_permutation_probe.py` tries all 24 mappings of logical
  DATA/MAILBOX/ADDRESS/STATUS onto the four HPI address slots. Both the fast
  run (`local_artifacts\hpi_address_permutation_probe.log`) and reset-each run
  (`local_artifacts\hpi_address_permutation_probe_reset_each.log`) reported
  `match=0` for every mapping. The reset-each run left only the known
  non-authoritative `0x0011` artifact in two mappings that route DATA reads
  through the address-slot behavior. No permutation produced a real DATA,
  MAILBOX, or STATUS response.

## Critical Findings
1. CY7C67200 Host port power is supplied via a robust 5V rail, bypassing the internal 10mA charge pump.
2. `HPI_ADDRESS` (offset `0x008`) is a Write-Only register. Reading it always returns `0x0000`.
3. The previous "Uninitialized Host" error was caused by the firmware halting during a faulty HPI loopback probe, not by a physical hardware failure.
4. HPI is not globally write-only. Only the `HPI_ADDRESS` logical port is
   write-only; DATA, MAILBOX, and STATUS should support reads, but the current
   board state returns `0x0000` for all active HPI reads.

## Recommended Next Steps
1. Reprogram the normal root INT1-only image (`0x033328D9`) before returning
   to USB packet capture; the board is currently on the weak-pullup diagnostic
   image (`0x03332BFF`).
2. Run `scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235`
   before trusting any USB evidence.
3. Run the Beagle 12 packet analyzer with a simple known-good low/full-speed
   mouse or keyboard on the DE2-115 HOST path.
4. Next HPI step without an external analyzer: inspect CY7C67200 reset/clock
   and HPI boot-mode strap assumptions. Longer reset-low and post-release
   settle windows did not recover reads, and mailbox writes are now proven at
   the pins without producing readable STATUS/MAILBOX response. Reset-release
   sideband sampling shows reset affects `INT0`, but no post-release sideband
   activity appears. An exhaustive logical-port permutation sweep did not
   recover readback. The weak-pullup contrast proves the FPGA input path reads
   released DATA high, while active HPI reads drive or hold DATA low.
5. Verify `SOF` (Start of Frame) packet generation.
6. If enumeration stalls, compare descriptor packets with Terasic Host Demo packet logs to isolate firmware-level USB protocol issues.
