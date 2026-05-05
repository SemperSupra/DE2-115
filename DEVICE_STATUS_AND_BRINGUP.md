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

## Critical Findings
1. CY7C67200 Host port power is supplied via a robust 5V rail, bypassing the internal 10mA charge pump.
2. `HPI_ADDRESS` (offset `0x008`) is a Write-Only register. Reading it always returns `0x0000`.
3. The previous "Uninitialized Host" error was caused by the firmware halting during a faulty HPI loopback probe, not by a physical hardware failure.

## Recommended Next Steps
1. Use the current root INT1-only image for the immediate USB capture path.
2. Run `scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235`
   before trusting any USB evidence.
3. Run the Beagle 12 packet analyzer with a simple known-good low/full-speed
   mouse or keyboard on the DE2-115 HOST path.
4. Capture HPI read-cycle pins with an external logic analyzer using
   `local_artifacts\hpi_external_analyzer_channels.csv` for labels/pins and
   trigger on `OTG_RD_N` falling or `OTG_CS_N` low. The internal reference for
   that capture is `local_artifacts\hpi_live_source_probe_capture.txt`.
5. Verify `SOF` (Start of Frame) packet generation.
6. If enumeration stalls, compare descriptor packets with Terasic Host Demo packet logs to isolate firmware-level USB protocol issues.
