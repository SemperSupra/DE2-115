# SignalTap Debugging Strategy for DE2-115 Bring-Up

This project now has enough firmware-side evidence to make the next USB debug step hardware-specific. UART, Etherbone, and internal bridge debug prove that USB HPI writes are reaching the FPGA-side bus, while every CY7C67200 read still samples `0x0000`. Ethernet Port 1 is working in the forced-MII low-speed path; AUTO10/100, 100-only, and 10-only variants pass ping and Etherbone CSR stress.

## Current Debugging Infrastructure

- **UART:** Primary status channel on COM3 at 115200 baud.
- **LiteScope:** `hpi_analyzer` and `eth_analyzer` are instantiated for higher-level SoC capture.
- **ISSP/altsource_probe:** Present for `HPI0`, `ETH0`, `ETX0`, and `ARP0`; command-line STP reads work from elevated host PowerShell.
- **Quartus-native debug:** Preferred for external pin truth because Quartus runs on the Windows host with direct USB-Blaster access.
- **Capture files:** `signaltap/usb_hpi_capture.stp` and `signaltap/eth_rgmii_capture.stp` are the current repo-tracked sessions. Run them with elevated `quartus_stp.exe` on the host, not inside Docker.
- **Current limitation:** `signaltap/usb_hpi_capture.stp` has normalized
  `signal_set_1` / `log_1` names, but embedding it with `SIGNALTAP_FILE` still
  produces a SOF where `quartus_stp` reports no `auto_signaltap_0` instance.
  Use HPI0 source/probe or an external analyzer until a real `sld_signaltap`
  node is visible in the reports/SOF.
- **2026-05-04 HDL SignalTap result:** An explicit `sld_signaltap` instance in
  `cy7c67200_wb_bridge` does instantiate and fit when enabled, and the hidden
  SLD hub ports must be omitted rather than tied to constants. However, both
  tested hardware images failed Ethernet bring-up:
  checksum `0x0340C359` with a nonzero node id, and checksum `0x033C790F`
  with the default node id. The validated SOF was restored afterward and ping
  recovered. The HDL block is now guarded by `HPI_PIN_SIGNALTAP` so normal
  builds stay on the Ethernet-safe path.
- **2026-05-04 default-image recovery:** After guarding the HDL SignalTap block
  and removing QSF SignalTap assignments, the default root image compiled and
  programmed as checksum `0x033328D9`. Ethernet passed 50/50 ping plus 512 CSR
  loops after the gate was corrected to stress `lcd_out`; `leds_r_out` is not a
  valid sustained oracle because USB diagnostic idle firmware writes it as a
  heartbeat.
- **Working HPI capture wrapper:** `scripts\capture_hpi_source_probe.ps1` arms
  HPI0 source/probe mode `1`, triggers a DATA read through
  `scripts\hpi_capture_combined.py`, and decodes the captured 192-bit probe into
  `local_artifacts\hpi_source_probe_capture.txt`.
- **External analyzer cycle generator:** `scripts\hpi_cycle_loop.py` repeats
  HPI cycles over Etherbone on the Ethernet-safe image. Use
  `python scripts\hpi_cycle_loop.py --start-server --port 1235 --mode rw --count 0 --period-ms 100 --reset`
  while triggering the analyzer on `OTG_RD_N` falling or `OTG_CS_N` low.
- **One-command capture wrapper:** `scripts\run_hpi_external_capture_loop.ps1`
  runs the capture loop with optional Ethernet preflight and logs output. Use
  `powershell -ExecutionPolicy Bypass -File .\scripts\run_hpi_external_capture_loop.ps1`
  for the default continuous DATA write/read loop. The wrapper also writes
  `local_artifacts\hpi_external_analyzer_channels.csv` with the external
  analyzer signal labels and FPGA pins.
- **2026-05-05 live-loop internal reference:** While the continuous wrapper loop
  was running, HPI0 source/probe mode `1` captured
  `48FC8FF7C9D6823B80000000000000000000000000000000`, decoded in
  `local_artifacts\hpi_live_source_probe_capture.txt` as reset released,
  `CS_N=0`, `RD_N=0`, `WR_N=1`, `ADDR=0`, and all data fields `0x0000`.
  Use this as the internal reference for the external analyzer capture.
- **No-analyzer fallback:** `scripts\run_hpi_weak_pullup_diag.ps1` builds a
  diagnostic image with weak pull-ups on `usb_otg_data[15:0]`, programs it,
  runs the Ethernet gate, and repeats HPI write/read cycles. This is the
  replacement for an external DATA-bus capture when no logic analyzer is
  available.
- **No-analyzer contrast automation:**
  `scripts\run_hpi_no_analyzer_contrast.ps1` assumes the weak-pullup image is
  programmed and captures idle/released, reset-low, active-read, and sequential
  HPI port sweep evidence into
  `local_artifacts\hpi_no_analyzer_contrast.log`.
- **Weak-pullup result:** The weak-pullup image checksum `0x03332BFF` passed
  Ethernet and the fitter reported `Weak Pull Up = On` on all `usb_otg_data`
  pins. HPI DATA reads still returned all zeroes across eight cycles, so the
  zero readback is not explained by an undriven FPGA input floating low.
- **Weak-pullup contrast result:** Idle/released and reset-low HPI0 captures
  read `hpi_data=0xffff`/`sample_data=0xffff`, but active DATA reads with
  `CS_N=0`, `RD_N=0`, `WR_N=1`, `ADDR=0`, and reset released read
  `hpi_data=0x0000`/`sample_data=0x0000`. DATA, MAILBOX, STATUS, and
  non-authoritative ADDRESS read sweeps all returned `0x0000`.
- **Reset timing sweep:** `scripts\run_hpi_reset_timing_sweep.ps1` varies
  reset-low duration, post-release wait, access cycles, and sample offsets
  while keeping one Etherbone server alive. The 2026-05-05 run completed 108
  combinations and every DATA/MAILBOX/STATUS read stayed zero.
- **Board wiring facts:** `docs\CY7C67200_BOARD_WIRING_FACTS.md` records the
  local manual evidence. DE2-115 Figure 4-31 shows CY `XTALIN` fed by MAX II
  `EPM240` at `12MHz`; BIOS boot mode uses `GPIO30/GPIO31`; the current FPGA
  platform does not expose those boot pins.
- **Mailbox write-window probe:** `scripts\run_hpi_mailbox_sideband_probe.ps1`
  wraps `scripts\hpi_mailbox_sideband_probe.py` and uses HPI0 source/probe mode
  `6` to capture MAILBOX writes. The verified narrow run in
  `local_artifacts\hpi_mailbox_sideband_probe_rerun4.log` captured
  `0xfa50` with `CS_N=0`, `WR_N=0`, `RD_N=1`, `ADDR=1`, and all write data
  views equal to `0xfa50`. STATUS/MAILBOX reads after the write still returned
  zero and sidebands stayed idle (`INT0=1`, `INT1=1`, `DREQ=0`).
- **Reset-release sideband timeline:**
  `scripts\run_hpi_reset_release_sideband_timeline.ps1` samples HPI0 idle
  state while reset is low and after release. The first run showed reset-low
  `INT0=0`, `INT1=1`, `DREQ=0`; released samples through 2 seconds showed
  `INT0=1`, `INT1=1`, `DREQ=0`. Use it after any reset/boot-mode change.
- **HPI address permutation probe:** `scripts\hpi_address_permutation_probe.py`
  tries all 24 logical mappings of DATA/MAILBOX/ADDRESS/STATUS onto HPI address
  slots. The reset-each run in
  `local_artifacts\hpi_address_permutation_probe_reset_each.log` produced
  `match=0` for every mapping; only the known `0x0011` address-slot artifact
  appeared.

## Debug Priorities

### 1. USB HPI Readback

Current evidence:

```text
HPI DBG WR ... sample=00001234 cy=00001234
HPI DBG RD ... sample=00000000 cy=00000000
HPI0 read_data: rst=0 hpi_rst_n=1 cs_n=0 rd_n=0 wr_n=1 addr=0 data=0000
HPI0 live-loop probe: 48FC8FF7C9D6823B80000000000000000000000000000000
Beagle USB 12: on the DE2 HOST path with KVM2USB inline, active captures on the
project image and Terasic host mouse demo show repeated connect/disconnect/reset,
but no SOF/SETUP/IN/OUT packets. On the PC hub reference path, KVM2USB
enumerates in Windows as `VID_2B77&PID_3661` and Beagle sees SETUP,
descriptor DATA, ACK, and IN/NAK polling, although that inline reference still
resets repeatedly.
Terasic device-mode demo: `PC hub -> Beagle -> DE2 DEVICE Type-B` shows
`TGT_CONNECT/UNRST` followed by continuous `BAD_SYNC` and no valid packets, even
with KVM2USB removed from the DE2 HOST port and after reprogramming the Terasic
device demo.
```

Interpretation:

- FPGA HPI write drive is working.
- FPGA MAILBOX write drive is also working; HPI0 source/probe captured an
  intentional `0xfa50` write on `ADDR=1` with the expected active write
  strobes.
- FPGA reset control has an observable sideband effect: `INT0` is low while
  reset is asserted and returns high after release.
- HPI address-order confusion is unlikely: all 24 logical-port permutations
  failed to produce a valid DATA readback or readable STATUS/MAILBOX response.
- FPGA HPI read cycle is being issued.
- The CY7C67200 is not returning nonzero data at the FPGA pad sample point. An Etherbone reset/sample sweep from 0 to 60 cycles also returned only zeroes, so a simple sample-offset change is unlikely to fix it.
- With FPGA weak pull-ups enabled on `OTG_DATA[15:0]`, DATA reads still sample
  `0x0000`. If the bus were simply released, the weak-pullup image should have
  pushed reads toward `0xffff`.
- With the same weak-pullup image, idle/released and reset-low source/probe
  samples do read `0xffff`. The low value is specific to active HPI read
  cycles, not a general FPGA input or weak-pullup failure.
- A reset timing sweep through reset-low `0.01..2.0s` and post-release wait
  `0.1..2.0s` did not produce any nonzero DATA/MAILBOX/STATUS read.
- USB-line capture sees target presence/reset transitions but no host packets, so the CY is not reaching a functional USB-host state.
- The DE2 HOST path does not currently reach packet traffic even with the
  Terasic host mouse demo. Before more HID class work, repeat the Beagle test
  with a simple known-good low/full-speed mouse or keyboard and focus on CY
  reset/clock/power plus HPI readback if no packets appear.
- The DE2 DEVICE path also fails before descriptors with Terasic's demo. This
  shifts priority to cable/orientation/hub/connector/PHY/power validation before
  adding more SignalTap around higher-level USB firmware.

SignalTap should capture external pads, not only internal bridge state, but it
must first pass the Ethernet gate. Until then, external logic analyzer capture
or the weak-pullup diagnostic image is the safer route.

Signals:

- `usb_otg_data[15:0]`
- `usb_otg_addr[1:0]`
- `usb_otg_cs_n`
- `usb_otg_rd_n`
- `usb_otg_wr_n`
- `usb_otg_rst_n`
- `usb_otg_int0`
- `usb_otg_int1`
- `usb_otg_dreq`

Recommended trigger:

- Falling edge of `usb_otg_cs_n`, with qualifiers for `usb_otg_rd_n == 0` to isolate reads.
- Use a second capture for writes with `usb_otg_wr_n == 0`.

Goal:

- Confirm whether `OTG_DATA` is driven by the CY during reads.
- Confirm `RD_N`, `CS_N`, address, and reset timing at the actual pins.
- Confirm no bus contention during writes.

### 2. Ethernet Port 1 Baseline

Current evidence:

```text
INBAND=0000000B
ping 192.168.178.50: 200 sent, 200 received
ETHERBONE_CSR_STRESS_OK loops=4096
ETHERNET_LOW_SPEED_TEST_PASS
```

Interpretation:

- The previous "LiteEth in-band is zero" and "ping fails" blockers are resolved in the forced-MII low-speed path.
- AUTO10/100, 100-only, and 10-only have all passed the current regression. The current 10-only image also passed a longer 200/200 ping plus 4096 red-LED CSR loop run.
- Gigabit mode remains a backlog cleanup target, not the current blocker.

Signals:

- LiteEth MAC source/sink streams through `eth_analyzer`.
- RGMII RX/TX pads if MAC stream capture is inconclusive.

Recommended trigger:

- RX valid assertion on the MAC sink/source path.
- RGMII `rx_ctl` assertion for raw frame entry.

Goal:

- Keep `scripts/ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235` as the known-good regression test.
- Use `ETH0`/`ETX0` only when deliberately revisiting gigabit timing or investigating a low-speed regression.

### 3. VGA

VGA is not the current blocker. Only instrument if display regressions appear.

## Tooling Guidance

- Use native Quartus SignalTap/source-probe for external HPI/RGMII pin captures from the Windows host.
- Use LiteScope for Wishbone/MAC-level context once physical signaling is proven.
- Avoid simultaneous SignalTap/LiteScope/JTAGBone experiments unless the JTAG chain has been explicitly validated for that combination.
