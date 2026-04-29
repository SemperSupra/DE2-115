# Bench Topology: KVM2USB, COM3, Ethernet Port 1, Beagle 12

## Physical connections

```text
DE2-115 VGA output
  -> USB2KVM / KVM2USB video input

KVM2USB USB connection
  -> DE2-115 USB host port
  -> advanced test target only after simple host devices work

Host COM3
  -> DE2-115 UART console

Host Ethernet
  -> DE2-115 Ethernet Port 1

Total Phase Beagle 12
  -> packet-level USB evidence source

Webcam / AgentWebCam
  -> board physical observation
```

## Roles

### COM3

Primary firmware log path.

Use for:

```text
boot messages
HPI phase markers
read/write results
error codes
mode/switch reporting
```

### Ethernet Port 1

Primary host control and CSR path.

Use for:

```text
Etherbone
CSR loops
debug register reads
source/probe snapshots
board GPIO smoke tests
```

Ethernet passing is a precondition for trusting new LiteX USB builds.

### KVM2USB / AgentKVM2USB

Use in two ways:

1. VGA capture / visible output evidence.
2. Advanced USB target after the host path works with simple mouse/keyboard.

Do not use KVM2USB as the first USB host proof target.

### Beagle 12

Use as packet-level USB truth.

The Beagle 12 is especially important because UART/Etherbone can show that firmware attempted USB operations, but only Beagle capture proves that USB packets were actually emitted or received.

### AgentWebCam

Use for:

```text
board overview
LED state
7-seg state
LCD text
switch positions
cable state
power/reset state
short videos during tests
```
