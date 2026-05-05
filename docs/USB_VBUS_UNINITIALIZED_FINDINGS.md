# USB Host Port Debug Findings: The "Uninitialized Host" Mystery

## 1. 5V VBUS is Robust
Contrary to initial assumptions regarding the CY7C67200's internal 10mA charge pump, testing with a USB digital inline tester confirmed that the DE2-115 board supplies a robust `4.99V` directly to the USB Type-A host port from the board's main power rail. The hardware is physically capable of powering a standard USB keyboard without browning out.

## 2. Why Did the Terasic Host Demo Fail?
During the `Beagle 12` packet capture of the "known-good" Terasic Host Demo, the USB digital tester reported a `0.00A` current draw. The capture log showed an endless loop of `TGT_CONNECT/UNRST` followed by `TGT_DISCON; RESET;`.

This occurred because we only loaded the `.sof` (hardware bitstream) of the Terasic Demo, omitting the `.elf` (NIOS II software program). Without the software running:
- The CY7C67200 was never initialized.
- No `SOF` (Start of Frame) packets were generated.
- Internal data-line pull-down resistors were never activated.
- The connected keyboard detected 5V but saw floating data lines with no host activity, causing it to immediately enter **USB Suspend Mode** (drawing <2.5mA, which registers as 0.00A on the tester).
- The Beagle 12 analyzer logged the physical connection but correctly saw the keyboard dropping off the bus.

## 3. Why Did the LiteX Firmware Fail?
Our custom LiteX firmware was also failing to initialize the CY7C67200. During the bring-up sequence, the `cy7c67200_bringup.c` code ran a Phase 1B "Hardware Loopback" test (`CY_STAGE1B_HW_LOOPBACK`) which attempted to write `0x1234` to the `HPI_ADDRESS` register (offset `0x008`) and read it back.

According to the CY7C67200 Datasheet, the `HPI_ADDRESS` register is **Write-Only** from the perspective of the HPI port. Reading it will always return `0x0000`.

Because the read returned `0x0000` instead of `0x1234`, our firmware assumed the chip's HPI interface was dead, logged `CY_BRINGUP_FAIL_HW_LOOPBACK`, and intentionally halted the CPU in an infinite loop. The firmware never reached the `SIE1_INIT` stage, leaving the CY7C67200 uninitialized and the USB port inactive.

## 4. The CY7C67200 HPI Readback Boundary
By running `usb_hpi_host_diag.py`, HPI0 source/probe, and the weak-pullup
diagnostic image, we proved that the FPGA input path can read the HPI DATA bus
high. With `WEAK_PULL_UP_RESISTOR ON` for `usb_otg_data[15:0]`, idle/released
and reset-low captures read `0xffff`, while active HPI reads still sample
`0x0000`. This narrows the blocker to active CY/board read behavior or
CY reset/clock/HPI boot-mode state, not to a globally floating FPGA input.

## 5. Resolution and Patch
1. The faulty `CY_STAGE1B_HW_LOOPBACK` test has been completely removed from `firmware/src/cy7c67200_bringup.c`.
2. The firmware and SoC bitstream have been rebuilt (`build/terasic_de2_115/gateware/terasic_de2_115.sof`).
3. The firmware will now safely bypass the loopback and proceed directly to `SIE1_INIT`, initializing the Host port and activating the USB bus.

## 6. 2026-05-03 Follow-up
The bypass is useful diagnostically but does not prove host initialization.
Latest UART evidence still shows CY register and RAM reads returning `0x0000`,
LCP handshake failure, and `SIE1_INIT NOACK`. A patched image with `hpi_data_oe`
exposed in the HPI debug probe compiled and programmed, but failed the Ethernet
acceptance gate, so USB packet evidence from that image is not trusted.

The board was restored to the validated Ethernet image
`de2_115_vga_platform_eth10_switchfix_validated_20260427.sof` afterward; that
image passed 50/50 ping and 512 Etherbone CSR loops.

## 7. 2026-05-03 Diagnostic-Idle Isolation
The firmware now separates "continue to host SIE path" from "do not block the
board after a USB diagnostic failure." The default image logs the HPI failure
and enters `USB_DIAG_IDLE`; the SIE path is gated by `DE2_USB_RUN_HOST_PATH`.

Fresh image checksum `0x03364B4E` reached `USB_DIAG_IDLE` but still failed the
Ethernet acceptance gate. UART evidence:
- `ETHDBG boot inband=00000004`
- `CY_STAGE2_REG_READ_VALUES hwrev=0000 cpu=0000 pwr=0000`
- `CY_STAGE2_REG_READ_FAIL`
- `USB_DIAG_IDLE`

This keeps the HPI readback problem unchanged and shows the Ethernet failure is
not caused by later SIE polling. The current working board image is restored to
the validated Ethernet SOF checksum `0x033C9E9A`.

## 8. 2026-05-03 Ethernet-Only Isolation
The HPI/OE debug route was removed again for isolation and firmware was rebuilt
with `DE2_USB_SKIP_DIAG=1`, which logs `USB_DIAG_SKIPPED` and idles before any
CY7C67200 HPI access.

Fresh image checksum `0x0336F036` still failed the Ethernet acceptance gate:
- Windows ping reported `Destination host unreachable`.
- `litex_server` never accepted the Etherbone connection.
- UART showed `ETHDBG boot inband=00000000`, `USB_DIAG_SKIPPED`, and
  `USB_DIAG_IDLE`.

This proves the current blocker is a fresh-generated Ethernet baseline
regression, not USB/HPI traffic. The board was restored to the tracked
validated Ethernet SOF checksum `0x033C9E9A`, which passed 50/50 ping and 512
Etherbone CSR loops.

## 9. 2026-05-03 HPI Bridge Split Result
The clean `f8e6b9b` validation source is reproducible: a fresh rebuild produced
checksum `0x033C9E9A` and passed the Ethernet gate. Adding current firmware only
also passed with checksum `0x03374149`, proving the modular USB firmware and
skip-idle path are not the Ethernet regression source.

The failure isolated to small HPI bridge RTL drift:
- Both current bridge deltas, `.HPI_INT(hpi_int1)` plus extra `last_ctrl` debug
  fields, failed Ethernet with checksum `0x0334614A`.
- Extra `last_ctrl` debug fields alone failed Ethernet with checksum
  `0x0335BC98`.
- `.HPI_INT(hpi_int1)` alone, with `last_ctrl` restored to its zero tail,
  passed 50/50 ping plus 512 CSR loops with checksum `0x033328D9`.

USB can continue up the ladder on the INT1-only bridge route. Do not treat
passive HPI debug-bit exposure as harmless on this design; capture those signals
with SignalTap or an external analyzer unless a debug image is separately gated
through Ethernet first.

After applying the INT1-only bridge state to the main workspace, the first root
SOF checksum `0x033C59C8` still failed the Ethernet gate. The remaining drift
was the USB interrupt pin mapping: main had `int0=A6`, `int1=D5`, while the
passing split-test image used `int0=D5`, `int1=E5`. Restoring the platform to
`D5/E5` produced root checksum `0x033328D9`, which passed 50/50 ping plus 512
CSR loops. Root builds are usable again for USB evidence after the Ethernet
gate.

On the recovered root image, `usb_hpi_host_diag.py` still shows the same HPI
readback boundary: writes reach the bus (`sample=0x1234 cy=0x1234` after a
write), but normal memory reads return `0x0000`. A sample-offset sweep from
`0..12` and an access-cycle sweep from `4..63` did not produce a valid normal
read. The next useful evidence is an external or working SignalTap capture of
the read cycle to prove whether the CY7C67200 drives `OTG_DATA[15:0]` while
`OTG_RD_N` is asserted and the FPGA output is released.

`local_artifacts/hpi_read_capture.vcd` now provides embedded LiteScope evidence
for the recovered root image. During a DATA read, the FPGA asserts `CS_N=0` and
`RD_N=0`, leaves `WR_N=1`, selects `HPI_ADDR=0`, and keeps reset released, but
the internal HPI data sample remains `0x0000`. This shifts the next proof point
to physical CY pin drive/read data selection rather than Wishbone decode or a
missing FPGA read strobe.

`scripts\capture_hpi_source_probe.ps1` now gives a repeatable HPI0 source/probe
capture around that same DATA-read transaction. The decoded capture in
`local_artifacts\hpi_source_probe_capture.txt` shows `captured=1`, `match=1`,
`hpi_access=1`, reset released, `CS_N=0`, `RD_N=0`, `WR_N=1`, `HPI_ADDR=0`, and
`hpi_data/cy_o_data/sample_data=0x0000`. An attempted pin-level SignalTap build
still did not expose an `auto_signaltap_0` instance to `quartus_stp`, so the
remaining proof requires an external analyzer or a corrected SignalTap
instantiation path.
