# Gemini CLI Prompt: DE2-115 USB HPI / Beagle 12 Strategy

You are working in the existing SemperSupra/DE2-115 repository.

## Mission

Use the existing validated debug paths to isolate the CY7C67200 USB HPI/host problem.

Do not start by implementing HID or KVM2USB host support. The priority is to prove HPI read/control behavior and host-port packet behavior.

## Critical facts

- COM3 is connected to the DE2-115 UART.
- Ethernet is connected on DE2-115 Ethernet Port 1.
- VGA goes to USB2KVM/KVM2USB.
- KVM2USB USB connection is connected to the DE2-115 host port, but it is an advanced target, not the first proof target.
- AgentWebCam can capture board LEDs, 7-seg, LCD, switches, cabling, and reset/power state.
- Total Phase Beagle 12 is available.
- The USB device path has been confirmed using the Beagle 12.
- Therefore, do not treat the CY7C67200, oscillator, or general USB PHY as globally dead.
- The active fault domain is HPI read/control behavior and/or host-mode/host-port behavior.

## Must-read docs

Read:

```text
docs/USB_HPI_DEBUG_STRATEGY.md
docs/BEAGLE12_USB_PACKET_EVIDENCE_PLAN.md
docs/USB_KVM_UART_ETH_TEST_TOPOLOGY.md
docs/PHYSICAL_OBSERVABILITY_AND_SWITCH_STRATEGY.md
docs/AGENT_BRINGUP_RUNBOOK.md
docs/EVIDENCE_BUNDLE_SCHEMA.md
issues/USB_HPI_DEBUG_ISSUES.md
```

## Hard constraints

Before and after hardware-affecting changes, run the repo's Ethernet/GPIO baseline tests if available:

```powershell
python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235
python scripts\board_gpio_smoke_test.py --start-server --port 1239
```

Do not trust USB results from a build that fails the Ethernet baseline.

Avoid heavy new RTL instrumentation unless necessary. Prior debug changes may perturb placement and break Ethernet RX even when timing appears to pass.

Prefer existing mechanisms:

```text
COM3 logs
Etherbone/CSR reads
source_probe/HPI0
usb_hpi_host_diag.py if present
AgentWebCam captures
Beagle 12 packet captures
Terasic reference demo comparisons
```

## First tasks

1. Confirm the current repo contains this strategy overlay.
2. Record or add a note documenting that the USB device path has been confirmed with the Beagle 12.
3. Ensure the evidence bundle schema includes Beagle 12 captures.
4. Inspect existing HPI bridge/wrapper code for DATA output-enable visibility.
5. If missing, propose a minimal PR to expose HPI DATA OE, DATA OUT, DATA IN, and sample timing in existing debug snapshots.
6. Compare LiteX HPI wrapper/bridge against the Terasic reference.
7. Do not implement HID/KVM2USB host behavior until HPI readback or Terasic host traffic is proven.

## Acceptance criteria for a useful PR

- Small scope.
- Clear run instructions.
- No hidden or dot-file requirement.
- Evidence bundle location documented.
- Ethernet regression preserved.
- Beagle 12 result interpretation documented if USB packet captures are involved.
