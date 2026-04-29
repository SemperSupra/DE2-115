# USB HPI / Host Bring-up Issue Breakdown

## Issue 1: Record current validated baseline

Acceptance:

- Known-good SOF hash recorded.
- Ethernet Port 1 test command documented.
- Board GPIO smoke test command documented.
- AgentWebCam camera choice documented.
- Beagle 12 device-path success recorded as baseline evidence.

## Issue 2: Add or verify HPI-only deterministic firmware mode

Acceptance:

- HPI-only mode does not proceed to LCP/BIOS/SIE/HID.
- UART emits deterministic phase markers.
- Loop can run slowly enough for analyzers.
- Ethernet regression still passes.

## Issue 3: Expose HPI DATA output-enable and read ownership

Acceptance:

- Debug snapshot includes DATA OE, DATA OUT, DATA IN, CS_N, RD_N, WR_N, RST_N, ADDR, state, count, sample point.
- Read cycles show FPGA OE deasserted.
- Evidence bundle includes COM3 and source/probe results.
- Ethernet regression still passes.

## Issue 4: Preserve Beagle 12 USB device-path baseline

Acceptance:

- Capture file stored or referenced.
- Notes identify cable path, Beagle orientation, USB speed, and observed valid packets.
- Agent prompts know this path is confirmed.

## Issue 5: Run Beagle 12 PC reference capture

Acceptance:

- PC host -> Beagle 12 -> simple mouse/keyboard capture proves Beagle setup.
- SOF and SETUP evidence recorded.

## Issue 6: Run Terasic host demo with simple mouse/keyboard through Beagle 12

Acceptance:

- Beagle capture shows either SOF/SETUP or clear failure.
- Result is used to decide whether host-port path works independent of LiteX.

## Issue 7: Compare LiteX HPI wrapper/bridge to Terasic reference

Acceptance:

- Differences listed for reset, HPI mode, data OE, read/write strobe timing, address/data register order, interrupt/DREQ handling.
- No code change required unless the diff identifies a specific fix.

## Issue 8: Only resume LCP/SIE/HID after gate

Acceptance:

- HPI readback succeeds or Terasic host demo proves host traffic.
- Simple mouse/keyboard tested before KVM2USB.
- KVM2USB remains advanced target, not first proof target.
