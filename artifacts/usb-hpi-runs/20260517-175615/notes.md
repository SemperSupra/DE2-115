# Run Notes

## Goal
Terasic host demo with AgentUSB2KVM downstream HID injection

## Hardware topology
DE2-115 HOST USB-A -> Beagle 12 -> USB2KVM USB-A downstream HID

## Switch positions

## Commands run
- `python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235`
- `python scripts\board_gpio_smoke_test.py --start-server --port 1239`

## COM3 observations
Not used; Terasic reference demo runs via Nios/JTAG.

## Ethernet observations
Not applicable while Terasic reference SOF is loaded.

## HPI observations
Terasic demo was loaded with the host-native SREC/`nios2-gdb-server.exe` path
before this capture.

## Beagle 12 observations

- Reset observed: yes, repeated `TGT_DISCON; RESET`
- SOF observed: no
- SETUP observed: no
- Enumeration observed: no
- BAD_SYNC: no
- Other errors: none beyond repeated reset/connect state changes

## AgentWebCam observations

## Conclusion
With actual topology `DE2-115 HOST USB-A -> Beagle 12 -> USB2KVM USB-A`, the
Terasic reference demo still produces no host token traffic. The downstream
side repeatedly disconnects/resets/reconnects.

## Next action
Use direct AgentUSB2KVM HID injection during capture to confirm the control
side can send keyboard/mouse events while the Beagle observes the downstream
USB bus.
