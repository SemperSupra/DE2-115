# Total Phase Beagle 12 USB Packet Evidence Plan

## Purpose

The Beagle 12 should be used as the packet-level truth source for USB traffic. It complements, but does not replace:

- COM3 UART logs
- Etherbone / CSR reads
- source_probe / SignalTap / LiteScope
- AgentWebCam visual evidence
- AgentKVM2USB VGA capture

## Important update

The USB device path has been confirmed using the Beagle 12.

That means:

```text
The CY7C67200 and general USB electrical path are not globally dead.
The active fault is narrowed to HPI read/control behavior and/or host-mode/host-port behavior.
```

## Beagle 12 roles

### 1. Capture setup validator

Before relying on any DE2 capture, prove the Beagle orientation and capture settings with:

```text
PC host -> Beagle 12 -> simple USB mouse/keyboard
```

Expected evidence:

```text
connect
reset
SOF traffic
SETUP / descriptor requests
IN / interrupt traffic for HID
```

### 2. Device-path baseline

Preserve the confirmed device-path capture:

```text
PC host -> Beagle 12 -> DE2-115 USB device path running Terasic or known-good device demo
```

Expected evidence:

```text
valid USB packet traffic
valid sync
SETUP packets from host
no persistent BAD_SYNC
```

This becomes a known-good artifact proving that the CY/USB device path is alive.

### 3. Host-port isolation

Run:

```text
DE2-115 USB host port -> Beagle 12 -> simple USB mouse
DE2-115 USB host port -> Beagle 12 -> simple USB keyboard
```

Do this first with a Terasic host demo if available, then with LiteX only after the HPI path is improved.

Expected good evidence:

```text
host-driven reset
SOF packets
SETUP packets
descriptor requests
periodic INs after enumeration
```

Expected bad evidence:

```text
connect/disconnect only
reset only
no SOF
no SETUP
persistent idle
VBUS-related errors
```

## Capture file naming

Use deterministic names:

```text
beagle12-pc-reference-mouse-YYYYMMDD-HHMMSS.tdc
beagle12-de2-device-demo-valid-YYYYMMDD-HHMMSS.tdc
beagle12-terasic-host-mouse-YYYYMMDD-HHMMSS.tdc
beagle12-litex-hpi-only-YYYYMMDD-HHMMSS.tdc
beagle12-litex-host-mouse-YYYYMMDD-HHMMSS.tdc
beagle12-litex-host-kvm2usb-YYYYMMDD-HHMMSS.tdc
```

If exporting CSV/text summaries, use matching base names:

```text
*.csv
*.txt
*.json
```

## Evidence notes template

For each capture, record:

```text
Capture name:
Date/time:
Git commit:
SOF filename/hash:
Firmware mode:
USB direction:
Cable path:
Beagle orientation:
USB speed:
Device attached:
Switch positions:
COM3 log file:
Ethernet baseline result:
AgentWebCam snapshot/video:
Summary:
  Was reset observed?
  Was SOF observed?
  Was SETUP observed?
  Was enumeration attempted?
  Any BAD_SYNC?
  Any VBUS or disconnect events?
Conclusion:
```

## Decision rules

### If device path works but HPI reads return zero

Focus on:

```text
HPI bus ownership
HPI read timing
HPI mode/reset/boot state
LiteX/Terasic HPI differences
```

### If Terasic host demo produces SOF/SETUP

Then the host port and CY host mode are physically usable. Focus on LiteX HPI/LCP/SIE sequence.

### If Terasic host demo produces no SOF/SETUP

Then focus on:

```text
host-port VBUS
host connector/cable
CY host-mode setup
Terasic demo assumptions
board jumpers/straps
Beagle orientation
external device compatibility
```

### If LiteX host mode produces no packets but Terasic host mode works

Then focus on:

```text
HPI readback
LCP load/ACK
BIOS mailbox
SIE host init
interrupt handling
endpoint scheduling
```

## Agent rule

Agents may not claim USB host success from UART messages alone.

USB host success requires packet evidence from the Beagle 12 or an equivalent packet analyzer:

```text
SOF observed
SETUP observed
enumeration transaction observed
```
