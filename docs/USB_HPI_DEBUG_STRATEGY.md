# USB HPI Debug Strategy for DE2-115 / CY7C67200

## Purpose

Bring up the DE2-115 CY7C67200 USB path in a controlled, evidence-driven way.

The current priority is not HID behavior and not KVM2USB behavior. The current priority is:

```text
Can the FPGA reliably control and read the CY7C67200 through HPI?
```

The project should remain gated by known-good UART, Ethernet Port 1, board visual/GPIO, and packet-level USB evidence.

## Current working assumptions

The strategy assumes:

- COM3 UART is available for firmware logs.
- Ethernet Port 1 is available for Etherbone / CSR testing.
- AgentWebCam can observe LEDs, 7-seg, LCD, switches, and board/cable state.
- AgentKVM2USB can observe VGA and later act as an advanced USB host target.
- Total Phase Beagle 12 can capture USB packets.
- USB device path has been confirmed with the Beagle 12.
- HPI writes are visible at the FPGA/CY bridge level.
- HPI reads are still the main blocker if all CY register/memory reads return `0x0000`.

## Strategic consequence of Beagle-confirmed USB device path

Do not treat the CY7C67200, oscillator, or general board USB PHY as globally dead.

Instead, treat the active fault domain as:

```text
1. HPI read data bus ownership / tri-state / output-enable
2. HPI read-cycle timing/protocol
3. HPI mode, reset, boot, or firmware ownership state
4. Host-port-specific VBUS / connector / cable / port behavior
5. Mismatch between LiteX HPI bridge and Terasic reference wrapper
6. LCP / BIOS / SIE firmware only after HPI readback is proven
```

## Non-goals until HPI/host proof improves

Do not prioritize:

- HID parsing
- KVM2USB as the first host device target
- complex endpoint polling
- large new debug RTL payloads
- heavy SignalTap/LiteScope changes that perturb Ethernet placement
- LCP/SIE changes before HPI readback proof

## Main phases

### Phase 0: preserve known-good baseline

Before any code change that affects hardware, record:

```text
git commit
SOF filename
SOF hash
firmware hash if applicable
switch positions
COM3 availability
Ethernet Port 1 pass/fail
board visual/GPIO pass/fail
```

No USB result is trusted from a build that fails the Ethernet/GPIO baseline.

### Phase 1: HPI-only deterministic loop

Create or preserve an HPI-only firmware/debug mode:

```text
1. Configure HPI bridge timing.
2. Assert CY reset.
3. Release CY reset.
4. Wait.
5. Read CY status/revision/control registers.
6. Write deterministic memory patterns.
7. Read back those patterns.
8. Repeat at a slow, analyzer-friendly rate.
```

Do not proceed to LCP, BIOS, SIE host init, endpoint polling, HID, or KVM2USB until this is understood.

### Phase 2: HPI bus ownership proof

For every read transaction, capture:

```text
phase
state
count
hpi_addr
hpi_cs_n
hpi_rd_n
hpi_wr_n
hpi_rst_n
hpi_data_oe
hpi_data_out
hpi_data_in
sample_point
read_result
int0
int1
dreq
```

Acceptance:

```text
On read cycles:
  FPGA data output enable must be deasserted.
  RD_N and CS_N must be asserted for the expected interval.
  WR_N must remain inactive.
  sample point must occur while the CY is expected to drive data.
```

### Phase 3: host-port isolation with Beagle 12

Use the Beagle 12 to distinguish HPI/control failure from host-port failure.

Test matrix:

```text
A. Known-good PC host + simple mouse/keyboard + Beagle 12
   Purpose: confirm capture setup and device traffic.

B. Terasic USB device demo + Beagle 12
   Purpose: already confirmed; preserve as CY/USB device-path baseline.

C. Terasic USB host demo + simple mouse/keyboard + Beagle 12
   Purpose: prove DE2 host port and CY host mode independent of LiteX.

D. LiteX HPI-only build + Beagle 12
   Purpose: Beagle may show no packets; primary evidence remains HPI readback.

E. LiteX host init + simple mouse/keyboard + Beagle 12
   Purpose: only after HPI readback or Terasic host demo succeeds.

F. LiteX host init + KVM2USB + Beagle 12
   Purpose: advanced target only after simple host device works.
```

### Phase 4: Terasic reference comparison

Compare project code against working Terasic reference for:

```text
CY reset sequence
HPI mode selection / straps
HPI address and data register ordering
HPI data bus output-enable behavior
RD_N / WR_N / CS_N timing
host/device demo firmware assumptions
interrupt and DREQ usage
clock/reset assumptions
```

### Phase 5: LiteX LCP / BIOS / SIE

Only resume after:

```text
HPI reads return nonzero/expected values
or
Terasic host demo proves host-port USB packet traffic and HPI mismatch is isolated
```

## Recommended branch names

```text
usb-hpi-deterministic-debug
usb-beagle12-host-isolation
usb-hpi-oe-readback-fix
usb-terasic-reference-compare
```
