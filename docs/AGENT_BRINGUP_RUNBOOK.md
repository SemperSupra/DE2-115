# Agent Bring-up Runbook

## Golden rules

1. Preserve validated Ethernet/GPIO/visual baseline.
2. Do not trust USB results from a build that fails Ethernet Port 1 regression.
3. Use COM3, Etherbone, AgentWebCam, and Beagle 12 together.
4. Treat Beagle 12 packet captures as USB truth.
5. Do not chase HID/KVM2USB until simple host traffic is proven.
6. Keep changes PR-sized and revertable.

## Pre-run checklist

```text
Git commit recorded
SOF filename/hash recorded
COM3 connected
Ethernet Port 1 connected
AgentWebCam camera selected
Beagle 12 connected if USB packet evidence is needed
Switch positions recorded
VGA/KVM2USB connected if video evidence is needed
```

## Baseline commands

Adjust ports/paths to match the current repo scripts.

```powershell
python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235
python scripts\board_gpio_smoke_test.py --start-server --port 1239
```

## Visual capture

```powershell
agentwebcam list --limit 10
python scripts\visual_board_selftest.py --start-server --port 1238 --camera 1 --capture-backend agentwebcam --duration 10 --state-seconds 2 --hold 1 --width 1920 --height 1080 --fps 15
```

## USB packet evidence workflow

### PC reference

```text
PC host -> Beagle 12 -> simple mouse/keyboard
```

Save as:

```text
beagle12-pc-reference-mouse-YYYYMMDD-HHMMSS.*
```

### Device-path baseline

```text
PC host -> Beagle 12 -> DE2 device path
```

Save as:

```text
beagle12-de2-device-demo-valid-YYYYMMDD-HHMMSS.*
```

### Host path

```text
DE2 host port -> Beagle 12 -> simple mouse/keyboard
```

Save as:

```text
beagle12-terasic-host-mouse-YYYYMMDD-HHMMSS.*
beagle12-litex-host-mouse-YYYYMMDD-HHMMSS.*
```

## HPI-only firmware mode

Expected UART phases:

```text
HPI_PHASE RESET_LOW
HPI_PHASE RESET_HIGH
HPI_PHASE WRITE_ADDR
HPI_PHASE WRITE_DATA
HPI_PHASE READ_ADDR
HPI_PHASE READ_DATA
HPI_RESULT wrote=1234 read=....
```

Acceptance:

```text
Writes visible
Reads explainable
DATA OE correct during reads
No Ethernet regression
Evidence bundle complete
```

## Stop conditions

Stop and document if:

```text
Ethernet baseline fails
GPIO/visual baseline fails unexpectedly
Beagle capture setup cannot be validated with PC reference
HPI debug change perturbs Ethernet RX
SignalTap/LiteScope change causes placement-dependent failures
```
