# DE2-115 Device Status and Bring-Up Strategy

Date: 2026-04-26

This document tracks the full-board bring-up state. Use it with
`ETHERNET_BASELINE.md`, `FINDINGS.md`, and `HANDOFF.md` before changing device
integration.

## Status Legend

- **Validated:** Board-tested with repeatable evidence.
- **Working, needs regression:** Observed working, but still needs a repeatable
  automated or documented pass/fail test.
- **Integrated, unvalidated:** RTL/CSR/software hook exists, but no current
  board-level pass result.
- **Blocked:** Work exists, but a lower-level failure prevents functional use.
- **Not started:** No meaningful project-level bring-up yet.
- **Deferred:** Intentionally postponed to avoid destabilizing the current
  baseline.

## Device Matrix

| Device / Area | Current Status | Evidence | Additional Effort |
| --- | --- | --- | --- |
| USB-Blaster / JTAG programming | Validated | Quartus programmer configures the FPGA; validation images have been programmed from the host. | Keep host Quartus flow documented; avoid Docker/JTAG passthrough dependency for hardware debug. |
| Build flow / Quartus compile | Validated | Firmware, SoC generation, Quartus compile, and programming pass. | Add a one-command CI-style local build check later; current build still has unconstrained-clock warnings. |
| System clocks / reset | Working, needs regression | SoC boots; KEY0 reset is wired into CRG; firmware runs. | Add a simple boot counter/reset self-test and document expected LED/UART behavior. |
| VexRiscv CPU / LiteX SoC | Validated | Firmware executes; UART output and Etherbone CSR access work. | Add a firmware self-test summary banner with version/build mode. |
| SDRAM | Integrated, unvalidated | `GENSDRPHY` and `add_sdram()` are in the SoC and firmware runs with the generated image, but no explicit recent RAM test is recorded. | Add walking-bit, address-line, burst, and LiteX memory-test pass/fail output over UART and Etherbone. |
| UART / RS232 diagnostic port | Validated | COM3 at 115200 baud is the primary diagnostic channel. | Preserve as first-line debug; add a short serial loopback/throughput test if using full RS232 externally. |
| VGA | Working, needs regression | VGA output is documented as working with the text-console/test output. | Add a deterministic test pattern/text-screen mode and capture checklist. |
| Red LEDs | Validated | Etherbone regression stresses red LED CSR write/read for 512 loops; 10 Mbps image passed 4096 loops. | Keep red LEDs as stable CSR stress target. |
| Green LEDs | Working, needs regression | Firmware heartbeat uses green LEDs; host test can probe them but does not use them for sustained stress. | Add a firmware-owned LED pattern test and document ownership to avoid host/firmware contention. |
| 7-segment displays | Integrated, unvalidated | GPIO outputs for all eight displays are instantiated. | Add firmware and Etherbone digit-pattern test: all off, all on, `0`-`F`, walking segment. |
| Switches | Integrated, unvalidated | GPIO input for 18 switches is instantiated. | Add UART/Etherbone readback test and compare against manual switch patterns. |
| Pushbuttons | Partially used | KEY0 is reset; other button GPIO use is not documented. | Add debounced GPIO readback for KEY1-KEY3; keep KEY0 as reset unless intentionally changed. |
| LCD 16x2 character module | Integrated, unvalidated | LCD GPIO output is instantiated. | Add HD44780-compatible init, write `DE2-115 OK`, cursor/clear tests, and visual checklist. |
| Ethernet Port 1 10/100 | Validated | `AUTO10/100`, `100-only`, and `10-only` pass ping and Etherbone CSR stress. Tracked 10 Mbps validation image exists. | Keep `scripts/ethernet_low_speed_test.py` as regression gate before/after USB or clock changes. |
| Ethernet Port 1 1 Gb | Deferred | GTX pin/resource work is preserved, but current stable path forces MII/10-100. | Resume only after USB is stable; use `ETH0`/`ETX0` source-probe/SignalTap and fix timing/constraints. |
| Ethernet Port 0 | Not started | Current target is Port 1; PHY16 is treated as absent/floating in current evidence. | Audit cable/PHY address/pins, then repeat MDIO, link, ping, and Etherbone tests independently. |
| Etherbone remote CSR access | Validated | Identifier read and LED CSR stress pass through host `litex_server` bind port `1235`. | Keep as host-driven test backbone for remaining devices. |
| SD card | Integrated, unvalidated | `add_sdcard()` is present; docs identify SD as next high-value device after USB/Ethernet confidence. | Add block read/write self-test, CID/CSD read, multi-block transfer, and FAT/FatFS smoke test. |
| USB CY7C67200 HPI write path | Partially working | FPGA debug records write data such as `0x1234` at the HPI bus. | Preserve current bridge/register ordering; do not change LCP/SIE flow until readback works. |
| USB CY7C67200 HPI read path | Blocked | CY registers and memory read as `0x0000`; source/probe shows valid read strobes but data remains zero. | Capture external HPI pins with SignalTap/logic analyzer; compare with Terasic USB demo bitstream. |
| USB host mode Type-A | Blocked | Beagle USB 12 sees connect/disconnect/reset events but no SOF/SETUP/IN/OUT packets. | Fix HPI readback, then LCP load, `COMM_ACK`, `SIE1_INIT`, reset, connect message, and HID boot protocol. |
| USB device mode Type-B | Not started / blocked | User wants device mode, but HPI/CY readback blocks all CY7C67200 functional modes. | After HPI is fixed, bring up device demo path separately from host mode and test enumeration from PC. |
| Audio codec | Not started | No current codec/I2C/audio data path evidence. | Audit codec pins and I2C control, add register read/write where possible, then line-out tone and line-in loopback tests. |
| I2C control buses | Not started | No current board-level I2C validation. | Add minimal I2C master, scan expected devices, then use it for audio/video peripherals. |
| PS/2 keyboard/mouse ports | Not started | No current PS/2 RTL/firmware tests. | Add open-drain PS/2 receiver/transmitter, keyboard scancode test, mouse packet test. |
| IR receiver | Not started | No current IR capture test. | Add timer/capture input and decode NEC-style pulse timing with UART output. |
| SRAM | Not started | No current external SRAM controller/test. | Add simple async SRAM controller, then walking-bit/address/data retention tests. |
| Flash memory | Not started | No current flash controller/test. | Add read-ID/read-array first; defer erase/program until read path and write-protect behavior are confirmed. |
| EPCS / configuration flash | Not started | FPGA configuration works through JTAG; no application-level EPCS access is documented. | Treat as separate low-priority storage target; read ID/status before any write/erase work. |
| TV/video decoder input | Not started | No current decoder/I2C/video-capture path. | Bring up I2C first, read decoder ID/status, then capture stable color bars or known composite source. |
| Camera / CCD connector | Not started | No current camera/CCD capture path. | Audit connector/pixel clock/reset/I2C, then add small frame sampler or sync detector. |
| GPIO expansion headers | Not started | No current generic expansion test. | Add safe direction-controlled GPIO bank test using loopback jumpers; document voltage limits. |
| HSMC connector | Not started | No current HSMC test. | Start with pin audit and low-speed GPIO loopback; defer high-speed interfaces until constraints are clean. |
| SMA clock / external clock I/O | Not started | No current SMA clock tests. | Add frequency counter/test clock output, then document safe clocking and termination assumptions. |
| Second/full RS232 features | Partially covered | Current UART diagnostics work; full external RS232 loopback is not documented. | Add TX/RX loopback test if the board connector is used beyond diagnostics. |

## Bring-Up Principles

- Preserve the Ethernet low-speed baseline before each major change.
- Prefer one device and one failure boundary per bitstream.
- Every device needs a firmware UART result and, where possible, an Etherbone
  host-driven test.
- Add SignalTap/source-probe only at the first uncertain hardware boundary.
- Avoid write/erase operations on flash-like devices until read ID/status paths
  are proven.
- Keep hardware-observed facts in `FINDINGS.md` and next-turn instructions in
  `HANDOFF.md`.

## Recommended Bring-Up Order

### Phase 0: Preserve Baseline

Pass criteria:

- Program known-good or freshly built low-speed Ethernet image.
- Run:

```powershell
python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235
```

- Confirm UART boot banner and no new clock/timing failures.

### Phase 1: Finish Current Blockers

1. **USB HPI readback**
   - Capture external HPI read/write pins.
   - Compare against Terasic demo if needed.
   - Pass when CY control/status or memory readback returns expected nonzero
     values and memory write/read works.
2. **USB host mode**
   - Pass when LCP load verifies, mailbox commands ACK, `SIE1_INIT` ACKs, USB
     reset runs, Beagle sees SOF/SETUP traffic, and a low-speed/full-speed HID
     device enumerates.
3. **USB device mode**
   - Pass when a PC sees a stable USB device descriptor and basic control
     transfers complete.

### Phase 2: Deterministic Storage and Memory

1. **SDRAM explicit test**
   - Add walking-bit/address/burst tests and log a concise UART pass/fail.
2. **SD card block mode**
   - Read card ID/status.
   - Read/write a scratch block range.
   - Add a host-triggered Etherbone command or firmware self-test.
3. **FAT/FatFS**
   - Mount, create file, write/read/verify, delete.
4. **SRAM**
   - Add async SRAM controller and destructive memory test.
5. **Flash/EPCS**
   - Read ID/status first; only then plan controlled erase/write tests.

### Phase 3: Human I/O

1. **Switches and buttons**
   - UART and Etherbone readback with expected bit masks.
2. **7-segment displays**
   - Walking segment and hex digit pattern.
3. **LCD**
   - Initialize and print firmware version/IP/test result.
4. **PS/2**
   - Keyboard scancode test, then mouse packet test.
5. **IR**
   - Pulse timing capture, then protocol decode.

### Phase 4: Media Interfaces

1. **Audio codec**
   - I2C scan/readback.
   - Configure codec and generate line-out tone.
   - Add line-in loopback or ADC capture.
2. **TV decoder**
   - I2C ID/status.
   - Sync detect and frame/line counter.
3. **Camera/CCD**
   - I2C/control first, then pixel clock/sync capture.

### Phase 5: Expansion and High-Speed Cleanup

1. **GPIO headers**
   - Safe low-speed loopback tests.
2. **SMA**
   - Clock output/frequency counter tests.
3. **HSMC**
   - Pin audit, low-speed loopback, then any needed high-speed interface.
4. **Ethernet Port 0 and 1 Gb**
   - Port 0 gets independent MDIO/link/Etherbone validation.
   - 1 Gb work resumes only after low-speed Ethernet and USB are stable.

## Per-Device Test Template

For every device, add this to `FINDINGS.md` when validated:

```text
Device:
Build/image:
Pins/resources audited:
Firmware test:
Host/Etherbone test:
SignalTap/source-probe evidence:
Pass criteria:
Remaining caveats:
```
