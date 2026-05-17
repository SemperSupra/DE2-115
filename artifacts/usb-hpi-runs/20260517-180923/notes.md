# Run Notes

## Goal
Terasic host demo with direct HID injection through AgentUSB2KVM

## Hardware topology
DE2-115 HOST USB-A -> Beagle 12 -> USB2KVM USB-A downstream HID; PC controls KVM2USB HID injection interface

## Switch positions

## Commands run
- `powershell -ExecutionPolicy Bypass -File .\scripts\run_terasic_usb_host_demo_host.ps1 -TerminalSeconds 0`
- `python scripts\capture_beagle_events.py 80`
- `python scripts\inject_agent_kvm_hid.py`

## COM3 observations
Not used; Terasic reference demo runs via Nios/JTAG.

## Ethernet observations
Not applicable while Terasic reference SOF is loaded.

## HPI observations
Terasic demo was loaded with the host-native SREC/`nios2-gdb-server.exe` path.
The application download previously verified 80 KiB OK and started at
`0x000001B4`.

## Beagle 12 observations

- Reset observed: yes, repeated `TGT_DISCON; RESET`
- SOF observed: no
- SETUP observed: no
- Enumeration observed: no
- BAD_SYNC: no
- Other errors: none beyond repeated reset/connect state changes

Direct AgentUSB2KVM HID injection succeeded during the capture:

- keyboard interface found and sent `usb`
- touch interface found and sent center click
- mouse interface found and sent relative movement

## AgentWebCam observations

## Conclusion
The PC-side HID injection path works, but the DE2-115 host path remains
packet-silent. The Beagle sees downstream target reset/connect cycling and no
host-issued SOF/SETUP tokens.

## Next action
Inspect physical USB host power/VBUS/jumpers and CY7C67200 board-level host
power conditions. Do not resume LiteX LCP/SIE work until HPI Rung 1 is fixed.
