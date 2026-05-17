# Implementation Plan v4: USB HPI Recovery and Beagle Evidence

## 1. What Already Exists

- **Baseline:** Ethernet Port 1 (10 Mbps forced MII), COM3 UART diagnostics, and GPIO/Visual smoke tests are validated and working.
- **HPI Writes:** Proven at the pin level.
- **Firmware Bring-up Ladder:** Modularized, currently includes HPI reset, CY register probes, RAM test, and LCP load. Do not use `HPI_ADDRESS` readback as a loopback test; that port is write-only.
- **USB Device Path:** Confirmed alive with the Beagle 12 analyzer (CY7C67200 is not globally dead).
- **USB Debug Tooling:** Host HPI diagnostics and HPI0 source/probe decoding scripts are ready.

## 2. What Remains Missing

- **HPI Readback:** Read data bus ownership is failing; reads return `0x0000`.
- **HPI Bridge RTL Match:** Exact Tri-state / Output-Enable (OE) behavior during read cycles needs to be exposed and verified against Terasic's reference.
- **Host Port Isolation:** We still need to prove the CY7C67200 host port can emit `SOF`/`SETUP` packets using a known-good Terasic host demo before blaming the LiteX LCP/SIE firmware.

## 3. Next Three Safest Tasks

**Task 1: Capture Beagle 12 PC Reference and Terasic Host Demo**
- Prove Beagle 12 capture setup using a PC host and a simple USB mouse.
- Run the known-good Terasic Host Demo to a simple USB mouse to confirm the CY7C67200 host port is electrically functional and can emit packets independently of LiteX.

**Task 2: Expose HPI DATA Output-Enable (OE)**
- Update the RTL debug probes in `cy7c67200_wb_bridge.v` and `CY7C67200_IF.v` to explicitly capture the state of the data output-enable (`hpi_data_oe`) during read cycles to ensure the FPGA is releasing the bus.
- 2026-05-03: implement this in `rtl/`, not only the staged root files; `scripts/build_soc.sh` overwrites root/staged copies from `rtl/`.
- 2026-05-03: OE exposure was backed out again for isolation. Even without the
  OE probe, and even with firmware built as `DE2_USB_SKIP_DIAG=1`, fresh images
  currently fail the Ethernet acceptance gate. Treat the validated Ethernet SOF
  as the trusted board image until fresh-generation drift is isolated.

**Task 3: Refine HPI-only Deterministic Firmware Loop**
- Ensure the firmware stays in a slow, analyzer-friendly HPI read/write loop (Phase 1) without proceeding to LCP/SIE initialization until HPI readback is verified.
- 2026-05-03: default firmware now enters `USB_DIAG_IDLE` after HPI failure and
  does not run the host SIE path unless `DE2_USB_RUN_HOST_PATH=1` is provided at
  firmware build time.

**Task 4: Isolate Ethernet Regression in New Generated Images**
- Build a minimal image from the validated Ethernet source/settings and prove a
  fresh compile can reproduce the Ethernet gate before reintroducing USB
  diagnostics.
- Current negative control: checksum `0x0336F036`, built with
  `DE2_USB_SKIP_DIAG=1`, still failed Ethernet while UART showed no USB/HPI
  access beyond `USB_DIAG_SKIPPED`.
- Restoring `force_hpi_boot=0` to match the validated source did not change the
  failing checksum or recover Ethernet. Next isolate whether commit `f8e6b9b`
  can be freshly rebuilt and still pass.
- Clean `f8e6b9b` rebuild in `C:\tmp\de2_eth_baseline_f8e6b9b` reproduced
  checksum `0x033C9E9A` and passed 50/50 ping plus 512 CSR loops. Continue by
  adding post-validation drift back in controlled chunks: firmware-only first,
  then RTL HPI interrupt/debug changes.
- Split-test result: firmware-only drift passed Ethernet (`0x03374149`).
  Current bridge RTL with both INT1 routing and extra `last_ctrl` debug fields
  failed (`0x0334614A`). Debug fields only failed (`0x0335BC98`). INT1-only
  with the `last_ctrl` tail restored to zeros passed (`0x033328D9`).
- Strategy: keep `.HPI_INT(hpi_int1)` for the USB ladder, remove passive
  `last_ctrl` exposure of `hpi_int0/hpi_int1/hpi_dreq/diag_in`, and use
  SignalTap/external analyzer capture for those signals when needed.
- Main-workspace follow-up: the failing root SOF checksum `0x033C59C8` used the
  wrong USB interrupt pin mapping (`int0=A6`, `int1=D5`). Restoring the
  platform to the passing mapping (`int0=D5`, `int1=E5`) rebuilt the root image
  as checksum `0x033328D9`, and it passed 50/50 ping plus 512 CSR loops. Current
  root builds are trusted again for USB ladder work after the Ethernet gate.
- HPI ladder on recovered root image: `usb_hpi_host_diag.py` confirms write
  visibility (`sample=0x1234 cy=0x1234`) but normal reads remain `0x0000`.
  Sample-offset `0..12` and access-cycle `4..63` sweeps did not recover normal
  readback. Next evidence must come from external/SignalTap HPI read-cycle
  capture, not more blind timing sweeps.
- Embedded LiteScope evidence: `local_artifacts/hpi_read_capture.vcd` captured
  a DATA read with `CS_N=0`, `RD_N=0`, `WR_N=1`, `HPI_ADDR=0`, reset released,
  and internal sampled/read data still `0x0000`. The FPGA-side bridge is issuing
  reads and releasing the bus; next isolate CY-side data drive at the physical
  pins or with a pin-level SignalTap capture.
- HPI0 source/probe evidence: `scripts\capture_hpi_source_probe.ps1` arms mode
  `1` and captures the same DATA-read transaction. The decoded capture in
  `local_artifacts\hpi_source_probe_capture.txt` confirms `captured=1`,
  `CS_N=0`, `RD_N=0`, `WR_N=1`, `ADDR=0`, reset released, and
  `hpi_data/cy_o_data/sample_data=0x0000`.
- SignalTap limitation: `scripts\capture_hpi_pins.ps1` and the normalized
  `signaltap/usb_hpi_capture.stp` were exercised after a fresh Quartus compile,
  but the programmed SOF still has no `auto_signaltap_0` instance. Use the
  HPI0 source/probe wrapper for internal repeatability and an external analyzer
  for physical pad proof.
- Use the fixed `scripts/load_bitstream.ps1`; confirm the programmed checksum is
  the newest root SOF, not a stale `build/.../gateware` SOF.
- Acceptance remains: 50/50 ping and 512 Etherbone CSR loops before trusting any
  USB packet evidence.

## 4. Exact Commands for Baseline Gates

Run these before trusting any new USB build:

```powershell
python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235
python scripts\board_gpio_smoke_test.py --start-server --port 1239
```

## 5. Exact Beagle 12 Capture Cases

- **PC Reference (Validator):**
  - **Path:** `PC host -> Beagle 12 -> simple USB mouse/keyboard`
  - **Filename:** `beagle12-pc-reference-mouse-<timestamp>.tdc`
- **Terasic Host Demo (Isolation):**
  - **Path:** `DE2-115 USB host port (with Terasic SOF) -> Beagle 12 -> simple USB mouse/keyboard`
  - **Filename:** `beagle12-terasic-host-mouse-<timestamp>.tdc`
