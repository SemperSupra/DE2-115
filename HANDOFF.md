# DE2-115 Handoff - Status Update

Date: 2026-05-05
Workspace: `C:\Users\Mark\Projects\DE2-115`

## Executive Status

- **2026-05-03 USB resume note:** A patched USB diagnostic image was built to
  continue past the invalid `HPI_ADDRESS` readback loopback and expose
  `hpi_data_oe` in the HPI debug probe path. Firmware/SoC/Quartus builds
  completed and the image programmed, but it failed the Ethernet acceptance
  gate (`192.168.178.50` unreachable; `litex_server` never became ready).
  UART during boot still showed HPI reads returning zero:
  `CY_STAGE2_REG_READ_FAIL`, `CY_STAGE3_RAM_RW_FAIL`, `SIE1_INIT NOACK`.
  The tracked validation image
  `validation_images/de2_115_vga_platform_eth10_switchfix_validated_20260427.sof`
  was reprogrammed afterward and passed 50/50 ping plus 512 CSR loops, so the
  board is back on the known-good Ethernet baseline.
- **2026-05-03 follow-up isolation:** Firmware now has a default USB
  diagnostic-idle path: after an HPI failure it logs the debug registers and
  enters `USB_DIAG_IDLE` without running the host SIE path. The fresh image
  checksum `0x03364B4E` still failed the Ethernet gate, while UART confirmed
  `ETHDBG boot inband=00000004`, `CY_STAGE2_REG_READ_FAIL`, and
  `USB_DIAG_IDLE`. This isolates the current Ethernet regression to the new
  generated image/RTL build delta, not to SIE polling. The board was restored
  again to validated checksum `0x033C9E9A`, which passed 50/50 ping and 512
  CSR loops.
- **2026-05-03 Ethernet-only isolation:** A stricter build with
  `DE2_USB_SKIP_DIAG=1` never touches the CY7C67200 HPI path. That fresh
  checksum `0x0336F036` still failed Ethernet (`Destination host unreachable`;
  `litex_server` connection refused), while UART confirmed
  `ETHDBG boot inband=00000000`, `USB_DIAG_SKIPPED`, and `USB_DIAG_IDLE`.
  The board was restored to the validated checksum `0x033C9E9A` and again
  passed 50/50 ping plus 512 CSR loops. USB work is currently gated on
  recovering a fresh-generated Ethernet baseline.
- **2026-05-03 strap-isolation result:** Restoring `force_hpi_boot` to the
  validated source setting (`0`, board straps own CY boot selection) did not
  recover the fresh Ethernet-only build. The generated SOF checksum remained
  `0x0336F036` and ping still timed out. The board was restored again to
  checksum `0x033C9E9A`, which passed 50/50 ping and 512 CSR loops.
- **2026-05-03 reproducibility check:** A clean temporary worktree at commit
  `f8e6b9b` was rebuilt in `C:\tmp\de2_eth_baseline_f8e6b9b`. Quartus produced
  checksum `0x033C9E9A` again, and that freshly rebuilt SOF passed 50/50 ping
  plus 512 CSR loops. The current blocker is therefore source drift after the
  validated commit, not an unreproducible Quartus/toolchain result.
- **2026-05-03 drift split result:** Firmware-only drift on top of clean
  `f8e6b9b` passed Ethernet with checksum `0x03374149`, so the modular USB
  firmware and `DE2_USB_SKIP_DIAG=1` idle path are not the regression source.
  Adding both current HPI bridge RTL changes failed Ethernet with checksum
  `0x0334614A`. Restoring the interrupt route to `hpi_int0` while keeping the
  extra `last_ctrl` debug bits also failed with checksum `0x0335BC98`.
  Keeping only the USB interrupt route change (`.HPI_INT(hpi_int1)`) and
  restoring the `last_ctrl` tail to zeros passed 50/50 ping plus 512 CSR loops
  with checksum `0x033328D9`. Source now keeps INT1 and removes the fragile
  passive debug-bit exposure.
- **2026-05-03 main-workspace rebuild result:** The earlier root SOF checksum
  `0x033C59C8` failed because the main platform still mapped USB interrupts as
  `int0=A6`, `int1=D5`, while the passing split-test image used `int0=D5`,
  `int1=E5`. After restoring the platform mapping to `D5/E5`, the main
  workspace rebuilt and programmed as checksum `0x033328D9`. It passed 50/50
  ping plus 512 CSR loops. Root builds are trusted again with the current safe
  USB bridge state.
- **2026-05-03 USB HPI ladder result on recovered root image:** Host HPI diag
  runs over Etherbone on checksum `0x033328D9`. Writes are still visible at the
  FPGA/CY HPI data path (`HPI_HOST_AFTER_WRITE ... sample=0x1234 cy=0x1234`),
  but normal HPI reads still return `0x0000` (`HPI_MEM_RW_FAIL`). A sample
  offset sweep `0..12` and access-cycle sweep `4..63` did not recover normal
  reads. The swapped A1/A0 probe returned `0x0011` for most sample/access
  settings, but status/mailbox and normal data reads remain zero.
- **2026-05-03 HPI0 source/probe snapshot:** `quartus_stp` on HPI0 mode `3`
  captured `probe_data=42FCCFF319C41E801A0D00000000FFFF0000FFFFFFFF4240` after
  the timing sweep. Decoded highlights: `cy_o_int=1`, `hpi_int0=1`,
  `hpi_int1=1`, `hpi_dreq=0`, `hpi_rst_n=1`, bus idle strobes high
  (`hpi_cs_n=hpi_rd_n=hpi_wr_n=1`), `sample_data=0xffff`, `cy_o_data=0xffff`,
  `hpi_data=0xffff`, but `read_data=0x0000`. This supports the current boundary:
  bus idle/released can be high, but completed HPI reads still latch zero.
- **2026-05-03 HPI0 DATA-read source/probe capture:** Added
  `scripts\capture_hpi_source_probe.ps1`, which arms HPI0 mode `1`, triggers
  the CY RAM write/read transaction, and decodes the captured probe into
  `local_artifacts\hpi_source_probe_capture.txt`. Captured DATA-read highlights:
  `captured=1`, `match=1`, `hpi_access=1`, `hpi_rst_n=1`, `hpi_cs_n=0`,
  `hpi_rd_n=0`, `hpi_wr_n=1`, `hpi_addr=0`, `latched_we=0`, `count=8`,
  `sample_data=0x0000`, `cy_o_data=0x0000`, and `hpi_data=0x0000`.
- **2026-05-03 LiteScope read-cycle capture:** Updated
  `scripts/hpi_capture_combined.py` to the current HPI register map and captured
  `local_artifacts/hpi_read_capture.vcd` from the recovered root image. The
  capture triggered on `usb_otg_rd_n` falling during a DATA read after writing
  address `0x1000` and data `0x1234`; host readback remained `0x0000`. Decoded
  read-window evidence shows `CS_N=0`, `RD_N=0`, `WR_N=1`, `HPI_ADDR=0`,
  `HPI_RST_N=1`, `latched_we=0`, and `hpi_data/cy_o_data/sample_data/read_data`
  all `0x0000` during the active read. This proves the FPGA is issuing a read
  and not driving write data in that window; the remaining question is why the
  CY7C67200 is not driving nonzero read data for DATA/MAILBOX/STATUS accesses.
- **2026-05-04 SignalTap instantiation diagnosis:** Quartus accepts
  `ENABLE_SIGNALTAP ON` and `USE_SIGNALTAP_FILE usb_hpi_min_capture.stp`, but
  the `.stp` auto-insertion path still produces a hub-only
  `de2_115_vga_platform.sld`. An explicit HDL `sld_signaltap` in the HPI
  bridge is recognized, instantiates, and fits when its hidden SLD hub ports are
  omitted instead of tied to constants. Hardware testing showed that explicit
  SignalTap variants break Ethernet bring-up despite positive timing:
  checksum `0x0340C359` with nonzero node id and checksum `0x033C790F` with
  default node id both returned only `Destination host unreachable`. The board
  was restored to validated checksum `0x033C9E9A`, and 5/5 ping passed. The HDL
  SignalTap block is now guarded by `HPI_PIN_SIGNALTAP` so default builds do not
  accidentally use the Ethernet-breaking analyzer.
- **2026-05-04 post-SignalTap root recovery:** Rebuilt the default non-SignalTap
  root image after guarding `sld_signaltap` and stripping stale QSF SignalTap
  assignments. Quartus full compile passed with positive timing; programmed SOF
  checksum `0x033328D9`. The first Ethernet gate had 50/50 ping but failed the
  CSR stress because the test used `leds_r_out`, which `USB_DIAG_IDLE` firmware
  updates as a heartbeat. `scripts\ethernet_low_speed_test.py` now stresses
  firmware-stable `lcd_out` instead, and the rerun passed 50/50 ping plus 512
  CSR loops on checksum `0x033328D9`.
- **2026-05-04 current HPI ladder rerun:** Host-triggered HPI diagnostic on the
  programmed checksum `0x033328D9` still shows the same boundary:
  `HPI_HOST_AFTER_WRITE ... sample=0x1234 cy=0x1234`, but normal DATA read,
  MAILBOX, and STATUS remain `0x0000`; the swapped A1/A0 probe returns
  `0x0011`. `scripts\capture_hpi_source_probe.ps1` again captured a DATA read
  with `hpi_access=1`, reset released, `CS_N=0`, `RD_N=0`, `WR_N=1`,
  `ADDR=0`, `count=8`, and `hpi_data/cy_o_data/sample_data/read_data=0x0000`.
  The `CY7C67200_IF` tri-state condition is `assign HPI_DATA = HPI_WR_N ?
  16'hzzzz : tmp_data`; because the captured read window has `HPI_WR_N=1`, the
  FPGA should be releasing the bus. The remaining proof point is still physical
  pad capture of whether the CY drives `OTG_DATA[15:0]` during reads.
- **2026-05-04 analyzer loop tool:** Added `scripts\hpi_cycle_loop.py` to
  repeat HPI read/write cycles from the host without changing the bitstream.
  Smoke test on checksum `0x033328D9` passed as a tool run and reproduced the
  failure:
  `python scripts\hpi_cycle_loop.py --start-server --port 1235 --mode rw --count 3 --period-ms 50 --reset`
  emitted three `HPI_LOOP_RW` cycles with `read=0x0000`, `sample=0x0000`,
  `cy=0x0000`, `ctrl=0x03200800`. For external capture, run the same command
  with `--count 0 --period-ms 100` and trigger on `OTG_RD_N` falling or
  `OTG_CS_N` low.
- **2026-05-04 capture-loop automation:** Added
  `scripts\run_hpi_external_capture_loop.ps1`, a one-command wrapper that can
  run a quick Ethernet gate, print analyzer trigger/pin guidance, start the
  repeated HPI loop, and tee output to `local_artifacts`. Smoke test:
  `powershell -ExecutionPolicy Bypass -File .\scripts\run_hpi_external_capture_loop.ps1 -SkipEthernetGate -Count 2 -PeriodMs 50`
  completed and logged two `HPI_LOOP_RW` cycles with zero readback.
- **2026-05-05 capture pin-map automation:** Extended
  `scripts\run_hpi_external_capture_loop.ps1` to write
  `local_artifacts\hpi_external_analyzer_channels.csv` and print all analyzer
  labels with FPGA pins. Smoke test with `-Count 2 -PeriodMs 100` printed the
  `OTG_DATA[15:0]`, `OTG_ADDR[1:0]`, `OTG_CS_N`, `OTG_RD_N`, `OTG_WR_N`,
  `OTG_RST_N`, `OTG_INT0`, `OTG_INT1`, and `OTG_DREQ` mapping and again
  reproduced `read=0x0000`.
- **2026-05-05 live external-loop/source-probe result:** Started the continuous
  capture loop with
  `powershell -ExecutionPolicy Bypass -File .\scripts\run_hpi_external_capture_loop.ps1 -SkipEthernetGate -Count 0 -PeriodMs 100`
  and live log `local_artifacts\hpi_external_capture_loop_live.log`. The loop
  advanced past 400k write/read cycles with repeated
  `HPI_LOOP_RW ... read=0x0000 sample=0x0000 cy=0x0000 ctrl=0x03200800`.
  While that loop was active, `quartus_stp -t scripts\read_source_probe.tcl HPI0 1 3000 3`
  selected the HPI0 source/probe instance and captured stable
  `probe_data=48FC8FF7C9D6823B80000000000000000000000000000000`. Decoded
  highlights are saved in `local_artifacts\hpi_live_source_probe_capture.txt`:
  reset released, `CS_N=0`, `RD_N=0`, `WR_N=1`, `ADDR=0`, `captured=1`,
  `match=1`, and `hpi_data/cy_o_data/sample_data/read_data=0x0000`.
  This confirms the active loop is generating the intended internal DATA-read
  condition; the remaining evidence must come from the physical HPI pads.
- **2026-05-05 no-analyzer fallback:** Added a weak-pullup HPI DATA diagnostic.
  `DE2_USB_HPI_WEAK_PULLUPS=1 /workspace/scripts/build_soc.sh 1` now appends
  `WEAK_PULL_UP_RESISTOR ON` for `usb_otg_data[0]` through
  `usb_otg_data[15]`. `scripts\run_hpi_weak_pullup_diag.ps1` automates the
  weak-pullup SoC generation, Quartus compile, programming, Ethernet gate, and
  eight HPI write/read cycles. Interpretation: if HPI DATA reads become
  `0xffff` or mostly high, the CY7C67200 is not driving the read bus; if reads
  remain `0x0000`, the CY/board path is actively holding the bus low during
  reads.
- **2026-05-05 weak-pullup result:** Built the weak-pullup image and Quartus
  completed successfully at 17:53:43. The programmed SOF checksum was
  `0x03332BFF`. The fitter pin table confirms `Weak Pull Up = On` for
  `usb_otg_data[0]` through `usb_otg_data[15]`. Ethernet remained usable:
  49/50 ping plus 512 `lcd_out` CSR loops passed. Eight HPI DATA write/read
  cycles still returned `read=0x0000`, `sample=0x0000`, `cy=0x0000`,
  `ctrl=0x03200800`. This rules against a simple high-Z read bus floating low
  at the FPGA input; with weak pull-ups enabled, released lines should have
  sampled high. The next debug target is why the CY/board path is holding DATA
  low or not entering a readable HPI state.
- **2026-05-05 no-analyzer contrast result:** Added
  `scripts\hpi_set_reset.py` and `scripts\run_hpi_no_analyzer_contrast.ps1`.
  The contrast wrapper passed a 20/20 ping plus 128 `lcd_out` CSR Ethernet
  gate, captured idle/released and reset-low HPI0 source/probe, swept the HPI
  logical ports sequentially, and captured an active DATA read. The important
  split is now explicit: idle/released HPI0 reads
  `hpi_data=0xffff`, `cy_o_data=0xffff`, `sample_data=0xffff`; reset-low reads
  `hpi_rst_n=0`, `hpi_data=0xffff`, `sample_data=0xffff`; active DATA read has
  `CS_N=0`, `RD_N=0`, `WR_N=1`, `ADDR=0`, `hpi_rst_n=1`, but
  `hpi_data/cy_o_data/sample_data/read_data=0x0000`. Sequential DATA, MAILBOX,
  STATUS, and non-authoritative ADDRESS reads each returned `0x0000`. Log:
  `local_artifacts\hpi_no_analyzer_contrast.log`; active VCD:
  `local_artifacts\hpi_no_analyzer_active_read_capture.vcd`.
- **2026-05-05 reset timing sweep result:** Added
  `scripts\hpi_reset_timing_sweep.py` and
  `scripts\run_hpi_reset_timing_sweep.ps1` to test reset/boot-settle timing
  without restarting `litex_server` for every point. The run passed a 20/20
  ping plus 128 `lcd_out` CSR Ethernet gate and completed 108 rows:
  reset-low `0.01/0.1/0.5/2.0s`, post-release wait `0.1/0.5/2.0s`,
  access cycles `10/32/63`, and sample offsets `2/8/16`. DATA, MAILBOX, and
  STATUS read `0x0000` before and after a DATA write in every row
  (`nonzero=0x0000`). Log:
  `local_artifacts\hpi_reset_timing_sweep.log`. The command wrapper hit the
  agent's 180s timeout after the script printed `HPI_RESET_SWEEP_END`, so treat
  the log as the authoritative completed result.
- **2026-05-05 CY wiring fact check:** Added
  `docs/CY7C67200_BOARD_WIRING_FACTS.md` from local `de2_manual.pdf`,
  `bios_manual.pdf`, and `hw_notes.pdf`. The DE2 manual states that the
  CY7C67200 interface is set to HPI and Figure 4-31 shows CY `XTALIN` fed by a
  MAX II `EPM240` at `12MHz`, not by Cyclone IV user fabric. The BIOS manual
  says HPI co-processor boot is selected by `GPIO30=0/GPIO31=0`, while EEPROM
  stand-alone is `GPIO30=1/GPIO31=1`. The current platform does not expose
  documented `GPIO30/GPIO31` boot pins, so `force_hpi_boot` remains a stub and
  should not be treated as a real strap override.
- **2026-05-05 mailbox sideband/write-window result:** Added
  `scripts\hpi_mailbox_sideband_probe.py` and
  `scripts\run_hpi_mailbox_sideband_probe.ps1` to exercise MAILBOX writes while
  HPI0 source/probe captures idle, post-write idle, and a concurrent mailbox
  write window. The first full run passed the Ethernet gate and reproduced
  zero STATUS/MAILBOX readback. After fixing the concurrent capture timing, the
  narrow rerun
  `powershell -ExecutionPolicy Bypass -File .\scripts\run_hpi_mailbox_sideband_probe.ps1 -Log local_artifacts\hpi_mailbox_sideband_probe_rerun4.log -SkipEthernetGate -Values 0xfa50`
  captured the intended write: `captured=1`, `match=1`, `diag_src=0x000c`,
  `CS_N=0`, `WR_N=0`, `RD_N=1`, `ADDR=1`, reset released, and
  `write_data=sample_data=cy_o_data=hpi_data=0xfa50`. Idle captures still show
  `INT0=1`, `INT1=1`, `DREQ=0`; follow-up STATUS/MAILBOX reads still return
  `0x0000`. This confirms the FPGA drives MAILBOX writes correctly and the
  source/probe can catch the write window, but it does not show CY firmware/BIOS
  response to the mailbox command.
- **2026-05-05 reset-release sideband timeline:** Added
  `scripts\run_hpi_reset_release_sideband_timeline.ps1` to automate a
  no-analyzer reset/sideband probe. Rerun:
  `powershell -ExecutionPolicy Bypass -File .\scripts\run_hpi_reset_release_sideband_timeline.ps1 -Log local_artifacts\hpi_reset_release_sideband_timeline.log -SkipEthernetGate -DelaysMs 0,100,500,1000,2000`.
  Reset-low HPI0 decoded as `hpi_rst_n=0`, `INT0=0`, `INT1=1`, `DREQ=0`, and
  idle DATA high. After release, the coarse samples at
  `0/100/500/1000/2000ms` decoded as `hpi_rst_n=1`, `INT0=1`, `INT1=1`,
  `DREQ=0`, and idle DATA high. This proves the FPGA reset control has an
  observable CY-side effect, but it did not reveal post-release interrupt/DREQ
  activity that would imply a responsive HPI BIOS path.
- **2026-05-05 HPI address permutation sweep:** Added
  `scripts\hpi_address_permutation_probe.py` to try all 24 mappings of logical
  DATA/MAILBOX/ADDRESS/STATUS across the four HPI address slots. Fast run:
  `local_artifacts\hpi_address_permutation_probe.log`; reset-each run:
  `local_artifacts\hpi_address_permutation_probe_reset_each.log`. Both ended
  with `match=0`. The reset-each run produced only the known
  non-authoritative `0x0011` artifact in two mappings and no real DATA,
  MAILBOX, or STATUS response. This makes HPI address-order confusion unlikely
  to be the root blocker.
- **2026-05-05 live reset-release sideband watch:** Added
  `scripts\run_hpi_reset_release_live_sideband_watch.ps1` to keep HPI0
  source/probe running across CY reset release. The useful run used
  `-PreReleaseMs 4000` and logged
  `local_artifacts\hpi_reset_release_live_sideband_watch_prerelease4s.log`.
  Samples `0..19` decoded as reset-low: `hpi_rst_n=0`, `INT0=0`, `INT1=1`,
  `DREQ=0`, idle DATA high. Samples `20..29` decoded as released:
  `hpi_rst_n=1`, `INT0=1`, `INT1=1`, `DREQ=0`, idle DATA high. No short
  sideband pulse or DREQ activity was observed at this sampling rate.
- **2026-05-05 Cypress boot-strap note:** `docs\CY7C67200_BOARD_WIRING_FACTS.md`
  now records the local `hpi_manual.pdf` warning that `GPIO30/GPIO31` are also
  I2C lines and may power up high due to pull-ups, selecting standalone/EEPROM
  behavior unless the board actively straps them otherwise. This sharpens the
  remaining board-level question: what does the DE2-115 actually do to those
  pins at reset?
- **2026-05-06 strap/clock checklist:** Added
  `docs\CY7C67200_STRAP_CLOCK_CHECKLIST.md` as the concrete no-analyzer next
  step. The checklist focuses on the actual CY `GPIO30/GPIO31` reset strap and
  EEPROM path, MAX II `12MHz` delivery to `XTALIN`, and any board-level source
  that could hold `OTG_DATA[15:0]` low during active HPI reads. Do not spend
  more time on HPI timing/address permutations until one of those board-level
  facts changes.
- **2026-05-06 schematic strap result:** DE2-115 Rev D schematic sheet 20 shows
  `SCL/GPIO31` and `SDA/GPIO30` strapped low by fitted `10K` pulldowns
  (`R253`, `R254`), with the optional `10K` pullups marked `DNI`
  (`R251`, `R252`). The sheet's boot table says `0/0 = HPI` and labels
  `Default Setting: HPI mode`. This makes standalone/EEPROM boot less likely
  unless the physical board population differs; the next board-level target is
  now MAX II `USB_12MHz`, CY/USB power-reset health, and active-read DATA bus
  behavior.
- **2026-05-03 tool note:** `scripts/build_soc.sh` now stages generated
  Quartus host inputs (`.qsf`, `.sdc`, top Verilog, VexRiscv, init files) into
  the repo root. `scripts/load_bitstream.ps1` now selects the newest candidate
  `.sof` from root/build paths; previously it silently programmed a stale
  `build/.../gateware` SOF while the fresh Quartus output was at repo root.
- **UART:** Working on COM3 at 115200 baud and used for all current board diagnostics.
- **VGA:** Working and stable enough for bring-up.
- **Ethernet:** Port 1 is now working in forced-MII low-speed mode. AUTO10/100, 100-only, and 10-only variants each passed 50/50 ping to `192.168.178.50` plus 512 Etherbone red-LED CSR write/read loops through `litex_server` on host TCP port `1235`. The current 10-only image also passed a longer 200/200 ping plus 4096 red-LED CSR loop regression.
- **GPIO/visual self-test:** The current AUTO10/100 image includes board-test
  hooks for LEDs, switches, 7-seg, and LCD. Host GPIO smoke test passed, and
  `agentwebcam` camera `1` captured board screenshots/video during the visual
  self-test. The switch pin map has been corrected; all aligned switches now
  read `0x00000000`.
- **Saved image:** The current 10-only validation `.sof` is tracked at
  `validation_images/de2_115_vga_platform_eth10_switchfix_validated_20260427.sof`
  with SHA256
  `653CBED08D4C91ABF81BCFD7B708D980828A67BBF8C49A840DA07FA2007DBE67`.
- **Preservation manifest:** `ETHERNET_BASELINE.md` now records the working
  Ethernet settings, code paths, build commands, validation results, and
  regression rule in one place.
- **Board-wide device plan:** `DEVICE_STATUS_AND_BRINGUP.md` records the
  status of each DE2-115 device and the staged strategy for remaining bring-up.
- **USB HPI:** The FPGA-side HPI bridge now decodes the USB window correctly, uses Terasic-style registered HPI control/data timing, and successfully drives write data onto the bus. HPI is not globally write-only: only `HPI_ADDRESS` is write-only. DATA, MAILBOX, and STATUS reads are expected to work, but the CY7C67200 still returns `0x0000` on all active read attempts, including basic control registers and memory readback, so LCP/BIOS ACK still fails. Etherbone-driven reset and HPI sample-offset sweeps also returned only zeroes.
- **Current programmed board image:** Weak-pullup diagnostic image from
  the main workspace root, checksum `0x03332BFF`, with FPGA weak pull-ups
  enabled on `usb_otg_data[15:0]`. It passed the latest 20/20 ping plus 128
  Etherbone CSR loop contrast gate and earlier 49/50 ping plus 512 CSR gate.
  The normal root USB image checksum remains `0x033328D9`, and the tracked
  fallback validation SOF remains
  `validation_images/de2_115_vga_platform_eth10_switchfix_validated_20260427.sof`
  checksum `0x033C9E9A`.

## Changes Since Previous Handoff

- Default Ethernet port changed from 0 to 1 in `de2_115_vga_target.py`, `scripts/build_soc.sh`, and `run.bat`.
- Fixed USB Wishbone local address decode in `cy7c67200_wb_bridge.v`; LiteX supplies absolute Wishbone word addresses, so the bridge now decodes only the local low bits inside the 64 KiB USB window.
- Corrected HPI register order in firmware to match Terasic references:
  - A=0: data
  - A=1: mailbox
  - A=2: address
  - A=3: status
- Ported `CY7C67200_IF.v` to the registered Terasic HPI boundary style and routed the bridge outputs through it.
- Added USB diagnostics for write-cycle and read-cycle debug registers, CY register probes, mailbox/status reads, and command ACK failures.
- Added MDIO diagnostics for PHY16/PHY17 ID, basic status, PHY-specific status, RGMII delay register, and LiteEth in-band status.
- Added a dedicated `eth_gtx_clocks` platform resource so RGMII gigabit TX clock uses `ENET1_GTX_CLK` (`C23`) instead of the base LiteX `ENET1_TX_CLK` (`C22`) resource.
- Changed RGMII TX clocking to use the existing 90-degree PLL output (`eth_tx_ps`) and changed firmware MDIO setup to keep PHY TX internal delay off while keeping PHY RX delay on. Current PHY17 RGMII delay register after this change is `0C62`.
- Added Ethernet firmware diagnostics for LiteEth MAC RX/TX state, event pending bits, preamble errors, CRC errors, and in-band status. The firmware clears the unused software-MAC RX pending event after each diagnostic dump.
- Removed unverified USB DACK pin assignment from the custom platform resource and narrowed OTG DREQ to manual-backed `J1`; current Quartus pin report contains no `usb_otg_dack` pins.
- Added command-line source/probe debugging for `HPI0`, `ETH0`, `ETX0`, and `ARP0`; this works from elevated host Quartus STP without the GUI.
- Added forced-MII support in the custom RGMII PHY path and validated Ethernet with ping and Etherbone.
- Added low-speed Ethernet firmware selection through `DE2_ETH_SPEED_MODE`:
  default AUTO10/100, `100`, and `10`.
- Added `scripts/ethernet_low_speed_test.py` to run the repeatable low-speed
  Ethernet regression: ping, `litex_server`, LiteX identifier read, green LED
  CSR probe, and red LED CSR write/read stress.
- Added firmware board-test hooks that print a `BOARDTEST` banner and exercise
  red LEDs, green LEDs, eight 7-segment display CSRs, LCD GPIO, and optional
  SDRAM scratch testing.
- Corrected the DE2-115 switch pin map: `SW[2]` is `AC27`, `SW[3]` is `AD27`,
  and `AD28` is not a switch pin (`HSMC_CLKOUT0` in Terasic references).
- Added `scripts/board_gpio_smoke_test.py` for repeatable Etherbone GPIO smoke
  testing.
- Added `scripts/visual_board_selftest.py` for host-driven LCD text, LED/7-seg
  visual patterns, and `agentwebcam` screenshot/video capture.
- Added `scripts/capture_uart.py` for bounded UART boot-log capture.
- Added `scripts/usb_hpi_host_diag.py` for host-triggered CY7C67200 HPI
  reset/write/read diagnostics over Etherbone.
- Added `scripts/decode_hpi_probe.py` to decode the 192-bit `HPI0`
  source/probe value.
- Normalized `signaltap/usb_hpi_capture.stp` log/display names to `log_1` /
  `signal_set_1` and added `scripts\capture_hpi_pins.ps1`. Rebuilding and
  programming the attempted SignalTap image reproduced the known limitation:
  Quartus still includes only the SLD hub/fabric, and `quartus_stp` reports no
  `auto_signaltap_0` instance in the programmed SOF.
  `scripts\capture_hpi_source_probe.ps1` is the working repeatable HPI capture
  path until a true pin-level SignalTap node or external analyzer is available.

## Latest Verified Board Log

Key lines from the earlier AUTO10/100 board-test image programmed on 2026-04-26 at
17:20:13, checksum `0x033CA203`:

```text
Ping statistics for 192.168.178.50:
    Packets: Sent = 50, Received = 50, Lost = 0 (0% loss)

IDENT_PREFIX 'LiteX VGA Test SoC on DE'
ETHERBONE_CSR_STRESS_OK loops=512 ...
ETHERNET_LOW_SPEED_TEST_PASS

SWITCHES 0x00000000
LEDS_R_RW_OK
LEDS_G_PROBE 0x0000005a
SEVEN_SEG_RW_OK
LCD_GPIO_RW_OK
BOARD_GPIO_SMOKE_TEST_PASS
```

Current programmed corrected 10 Mbps image, programmed on 2026-04-27 at
06:33:00, checksum `0x033C9E9A`:

```text
Ping statistics for 192.168.178.50:
    Packets: Sent = 50, Received = 50, Lost = 0 (0% loss)

IDENT_PREFIX 'LiteX VGA Test SoC on DE'
ETHERBONE_CSR_STRESS_OK loops=512 ...
ETHERNET_LOW_SPEED_TEST_PASS

SWITCHES 0x00000000
LEDS_R_RW_OK
LEDS_G_PROBE 0x0000005a
SEVEN_SEG_RW_OK
LCD_GPIO_RW_OK
BOARD_GPIO_SMOKE_TEST_PASS
```

Visual self-test artifacts from `agentwebcam` camera `1`:

```text
SCREENSHOT local_artifacts\screenshots\board_visual_selftest_20260426_172358.jpg
VIDEO local_artifacts\videos\board_visual_selftest_20260426_172358.mp4
CROP local_artifacts\screenshots\board_visual_selftest_20260426_170047_switches_red_leds_7seg.jpg
CROP local_artifacts\screenshots\board_visual_selftest_20260426_170047_lcd.jpg
CROP local_artifacts\screenshots\board_visual_selftest_20260426_170047_device_leds_connectors.jpg
```

USB evidence from the current blocker remains:

```text
ETHDBG poll inband=0000000B ...
ETHARP op=0001 sha=50:EB:F6:7F:C6:1C spa=192.168.178.27 tha=00:00:00:00:00:00 tpa=192.168.178.50
HPI CFG: 000208FD
CY rev=0000 cpu=0000 pwr=0000 mb=0000 st=0000
HPI DBG WR cfg=000208FF ctrl=03601000 sample=00001234 cy=00001234
HPI DBG RD cfg=000208FF ctrl=03200800 sample=00000000 cy=00000000
MEM CHECK: 0000 FAIL
LCP...
FAIL
SIE1_INIT NOACK mb=0000 st=0000
USB_RESET NOACK mb=0000 st=0000
```

Host-triggered HPI diagnostic over Etherbone:

```text
HPI_HOST_CFG 0x000208ff
HPI_HOST_AFTER_WRITE cfg=0x000208ff ctrl=0x03200e00 sample=0x0000 cy=0x0000
HPI_HOST_AFTER_READ cfg=0x000208ff ctrl=0x03200e00 sample=0x0000 cy=0x0000
HPI_HOST_RESULT addr=0x1000 wrote=0x1234 read=0x0000 status=0x0000 mailbox=0x0000
HPI_HOST_MEM_RW_FAIL
```

Command-line HPI source/probe during a DATA read showed:

```text
Reset/sideband: rst=0 hpi_rst_n=1 int0=1 int1=1 dreq=0 cy_o_int=1
HPI pins: cs_n=0 rd_n=0 wr_n=1 addr=0 data=0000
Data: read=0000 sample=0000 last_sample=0000 cy_o=0000
```

Interpretation:

- USB writes are electrically visible at the FPGA HPI data pins (`0x1234` during the write cycle).
- USB reads are not returning CY7C67200-driven data; the sampled bus remains zero.
- Ethernet has moved past pinout/link detection and is usable for ping and Etherbone CSR transactions in AUTO10/100, 100-only, and 10-only low-speed modes.
- Beagle USB 12 inline capture on the DE2-115 USB HOST path sees target
  connect/disconnect/reset events but no USB packets. Passive captures with both
  this image and the Terasic USB host demo produced no SOF/SETUP/IN/OUT traffic
  on the DE2 host path.
- Active Beagle capture on 2026-04-27 with the KVM2USB inline produced 50
  events over roughly 73 seconds on the project image: repeated
  `TGT_CONNECT/UNRST` followed by `TGT_DISCON; RESET`, with no SOF/SETUP/IN/OUT
  packets. Repeating the same capture after programming Terasic's
  `DE2_115_NIOS_HOST_MOUSE_VGA.sof` produced the same no-packet pattern. This
  makes the immediate question physical/device-path compatibility, not just our
  HPI firmware.
- KVM2USB direct-to-PC validation through a USB hub succeeded at the Windows
  device level: `KVM2USB 3.0`, `KVM2USB 3.0 Config`, `VID_2B77&PID_3661`
  composite, and related HID/vendor-defined interfaces all report `OK`. A
  Beagle reference trace in the PC-hub path shows `SETUP`, descriptor `DATA`,
  `ACK`, and `IN/NAK` polling, proving the analyzer and KVM2USB can produce
  packet-level traffic. That inline reference still resets repeatedly, so do not
  treat it as a stable long-run KVM2USB trace.
- Device-mode isolation with Terasic's `DE2_115_USB_DEVICE_LED.sof` now points
  at a lower-level DE2/CY/physical USB issue, not just LiteX firmware. With the
  DE2 DEVICE Type-B path connected through the Beagle to a PC hub and KVM2USB
  unplugged from the DE2 HOST port, Beagle sees `TGT_CONNECT/UNRST` followed by
  continuous `BAD_SYNC` events and no valid USB packets. Reprogramming the
  Terasic device demo did not change the trace. Windows previously showed
  `Unknown USB Device (Device Descriptor Request Failed)` on one hub, but after
  the clean Beagle capture no DE2/unknown device is present.

## Verified Build Commands

```powershell
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_firmware.sh'
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_soc.sh 1'
```

Speed-specific firmware builds:

```powershell
docker compose exec -T litex_builder /bin/bash -lc 'FIRMWARE_CFLAGS=-DDE2_ETH_SPEED_MODE=100 /workspace/scripts/build_firmware.sh'
docker compose exec -T litex_builder /bin/bash -lc 'FIRMWARE_CFLAGS=-DDE2_ETH_SPEED_MODE=10 /workspace/scripts/build_firmware.sh'
```

```powershell
C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_sh.exe --flow compile de2_115_vga_platform
```

Run Quartus from:

```powershell
C:\Users\Mark\Projects\DE2-115\build\terasic_de2_115\gateware
```

Program:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\load_bitstream.ps1
```

Ethernet regression:

```powershell
python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235
```

Board GPIO smoke test:

```powershell
python scripts\board_gpio_smoke_test.py --start-server --port 1239
```

Visual self-test capture through the physical board camera:

```powershell
python scripts\visual_board_selftest.py --start-server --port 1238 --camera 1 --capture-backend agentwebcam --duration 10 --state-seconds 2 --hold 1 --width 1920 --height 1080 --fps 15
```

## Remaining Work

1. Keep `scripts/ethernet_low_speed_test.py` as the acceptance gate before/after USB changes. The current programmed image is the weak-pullup diagnostic checksum `0x03332BFF`; the normal root image checksum is `0x033328D9`; the tracked corrected 10-only validation fallback remains checksum `0x033C9E9A`.
2. The next USB ladder step is CY clock, CY/USB power-reset, and physical
   board-population validation using
   `docs\CY7C67200_STRAP_CLOCK_CHECKLIST.md`. The Rev D schematic points to
   default HPI boot mode via `GPIO31/GPIO30` pulldowns, but `force_hpi_boot`
   remains only a stub tied to zero; the FPGA platform does not expose those
   strap pins, and the DE2 manual shows CY `XTALIN` comes from MAX II `EPM240`
   at `12MHz`, not the Cyclone IV. Use
   `scripts\run_hpi_no_analyzer_contrast.ps1`,
   `scripts\run_hpi_reset_release_live_sideband_watch.ps1`, and
   `scripts\hpi_address_permutation_probe.py --reset-each` to rerun proof only
   after a clock/power/strap-population/board-level change.
3. Do not add passive bridge status bits into `last_ctrl` for routine USB debug. The split test showed that exposing `hpi_int0`, `hpi_int1`, `hpi_dreq`, and `diag_in` there can break Ethernet RX despite timing meeting. Use SignalTap/external analyzer capture or a tightly gated debug image instead.
4. Embedded LiteScope, HPI0 source/probe, weak-pullup contrast, and mailbox
   write-window capture now prove the FPGA asserts read controls correctly,
   drives write data correctly, released/reset-low DATA reads high, and only
   active HPI read cycles sample zero. Without an external analyzer, move the
   next debug step to CY clock/HPI mode/boot straps and board-level DATA bus
   hold causes. Reset timing, confirmed mailbox writes, and reset-release
   sideband sampling did not recover readable CY STATUS/MAILBOX/DATA; neither
   did exhaustive logical-port permutation. The most concrete remaining
   no-analyzer target is the CY `GPIO30/GPIO31` strap/EEPROM path and MAX II
   `12MHz` clock ownership.
5. Run the next Beagle capture with a simple known-good low/full-speed USB
   mouse or keyboard connected through the Beagle to the DE2-115 HOST port.
   Terasic's host mouse demo is the preferred comparison image for that test.
   If that also shows only connect/disconnect/reset and no packets, debug the
   DE2 host-port hardware/cabling/power/CY reset-clock path before more HID
   class work.
6. Before more LiteX USB firmware work, resolve the device-path `BAD_SYNC`
   symptom with Terasic's device demo: verify Beagle cable orientation, try a
   short known-good USB 2.0 Type-B cable, try direct PC port versus hub, and
   inspect the DE2 USB power/PHY/connector path. A working Terasic device demo
   is the fastest proof that the CY7C67200 physical path is sane.
7. Once USB readback works, resume LCP load verification and mailbox ACK flow.
8. Keep gigabit Ethernet deferred in the backlog; later add a separate gigabit cleanup task using `ETH0`/`ETX0` captures.
9. Use `DEVICE_STATUS_AND_BRINGUP.md` as the board-wide backlog. Start SD card
   bring-up after USB is unblocked enough to avoid losing the hardware-debug
   thread.
10. To fully validate independent transitions for all 18 switches, manually walk
   each switch and record the `switches_in` CSR value. Current evidence
   validates the all-aligned vector `0x00000000` after correcting the pin map.
