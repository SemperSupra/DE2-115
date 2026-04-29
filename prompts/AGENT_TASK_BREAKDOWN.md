# Agent Task Breakdown

## Track A: documentation and evidence

Can run immediately.

- Install strategy docs.
- Record confirmed Beagle 12 USB device-path baseline.
- Create evidence bundle directory convention.
- Add run notes template.
- Add Beagle 12 capture naming convention.

## Track B: no-code physical tests

Can run immediately if hardware is available.

- PC reference capture through Beagle 12.
- Terasic device demo baseline capture preservation.
- Terasic host demo with simple mouse/keyboard through Beagle 12.
- AgentWebCam board photos/video for each test.

## Track C: HPI debug visibility

Can run after baseline is protected.

- Inspect HPI OE/read visibility.
- Add minimal debug snapshot fields if missing.
- Avoid heavy RTL additions.
- Run Ethernet regression before trusting result.

## Track D: Terasic reference comparison

Can run in parallel with Track C.

- Compare reset, mode, HPI register order, OE, timing, interrupts, DREQ.
- Produce a report before code changes.

## Track E: LCP/SIE/HID

Blocked until:

- HPI readback works, or
- Terasic host demo proves host traffic and LiteX-specific issue is isolated.

## Track F: KVM2USB host target

Blocked until:

- simple mouse/keyboard host path works.
