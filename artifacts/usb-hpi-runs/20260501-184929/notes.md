# Run Notes

## Goal
Task 1B: Terasic Host Demo Isolation (New Board)

## Hardware topology
DE2-115 host port (Terasic SOF) -> Beagle 12 -> simple USB keyboard

## Switch positions

## Commands run
- `python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235`
- `python scripts\board_gpio_smoke_test.py --start-server --port 1239`

## COM3 observations

## Ethernet observations

## HPI observations

## Beagle 12 observations

- Reset observed: Yes (physical disconnects/resets only)
- SOF observed: No
- SETUP observed: No
- Enumeration observed: No
- BAD_SYNC: No
- Other errors: Repeated `TGT_CONNECT/UNRST;` followed by `TGT_DISCON; RESET;`.

## AgentWebCam observations

## Conclusion
The brand new DE2-115 board exhibits the exact same failure on the USB HOST port using the known-good Terasic Host Demo. It fails to emit any `SOF` or `SETUP` packets, just like the previous board. This indicates a systemic design flaw, systemic manufacturing defect, or an undocumented jumper requirement for the DE2-115's USB Host port, rather than a single dead board. 

## Next action
Halt firmware debugging for USB Host mode. Investigate systemic issues with the DE2-115 CY7C67200 Host configuration (e.g. VBUS power supply, OTG strap pins) by reviewing the board schematics.
