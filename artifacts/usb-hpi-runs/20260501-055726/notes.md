# Run Notes

## Goal
Task 1B: Terasic Host Demo Isolation

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

- Reset observed: Yes (but only physical connection resets, no USB protocol resets)
- SOF observed: No
- SETUP observed: No
- Enumeration observed: No
- BAD_SYNC: No
- Other errors: `TGT_CONNECT/UNRST;` followed repeatedly by `TGT_DISCON; RESET;`. No actual USB packets observed.

## AgentWebCam observations

## Conclusion
The known-good Terasic Host Demo exhibits the exact same failure on the DE2-115 HOST port as our LiteX firmware. The Beagle 12 sees the target keyboard connect and disconnect repeatedly, but the CY7C67200 never emits `SOF` or `SETUP` packets. This indicates a physical issue with the CY7C67200 host port, power supply to the port, or a missing board jumper, rather than a bug in the LiteX HPI/LCP/SIE firmware stack.

## Next action
Investigate DE2-115 schematics for USB Host power or jumper settings (e.g. VBUS control), or declare the CY7C67200 host port defective/unusable on this specific board. Do not spend further effort debugging LiteX USB host firmware until the Terasic Demo can emit packets.
