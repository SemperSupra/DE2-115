# Codex CLI Prompt: DE2-115 USB HPI / Host Isolation

Work in the existing SemperSupra/DE2-115 repository.

## Objective

Implement and preserve an evidence-driven bring-up strategy for the DE2-115 CY7C67200 USB path.

The USB device path has already been confirmed using a Total Phase Beagle 12. Therefore, the goal is no longer to prove that the CY or general USB PHY is alive. The goal is to isolate:

```text
HPI read/control problem
and/or
USB host-mode/host-port problem
```

## Required approach

1. Read the strategy docs under `docs/`.
2. Keep changes PR-sized.
3. Do not implement HID or KVM2USB support first.
4. Prefer low-risk debug visibility over heavy instrumentation.
5. Preserve Ethernet Port 1 and board GPIO/visual baselines.
6. Use Beagle 12 packet evidence to prove USB host/device behavior.

## Hardware topology to assume

```text
COM3 -> DE2-115 UART
Ethernet -> DE2-115 Port 1
DE2 VGA -> USB2KVM/KVM2USB video input
KVM2USB USB -> DE2-115 USB host port
Webcam/AgentWebCam -> board LEDs/7-seg/LCD/switches
Total Phase Beagle 12 -> USB packet analyzer
```

## Preferred next code-level change

Inspect whether the HPI bridge exposes:

```text
hpi_data_oe
hpi_data_out
hpi_data_in
hpi_cs_n
hpi_rd_n
hpi_wr_n
hpi_rst_n
hpi_addr
state
count
sample point
```

If it does not, add the smallest possible debug visibility path through an existing source_probe/CSR/debug mechanism.

Do not add a large LiteScope/SignalTap block unless the docs and tests justify it.

## Required tests

When a hardware-affecting change is made, run or document:

```powershell
python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235
python scripts\board_gpio_smoke_test.py --start-server --port 1239
```

If those scripts are unavailable or changed, find the repo's current equivalent and document it.

## Beagle 12 rules

- USB host success requires packet evidence, not just UART logs.
- Look for SOF and SETUP.
- Store or reference Beagle captures in the evidence bundle.
- Keep the confirmed USB device-path capture as a baseline artifact.
- Use simple mouse/keyboard before KVM2USB as a host target.

## Output expected from this task

Produce one of:

1. A documentation-only PR that installs/refines the strategy.
2. A small debug-visibility PR for HPI DATA OE/readback.
3. A test-run artifact PR adding evidence from Beagle 12 / COM3 / Ethernet / AgentWebCam.
4. A Terasic-reference comparison report.

Do not do broad refactors.
