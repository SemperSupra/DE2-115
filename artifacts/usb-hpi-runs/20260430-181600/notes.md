# Run Notes

## Goal
Task 1A: PC Reference Validator

## Hardware topology
PC host -> Beagle 12 -> simple USB mouse/keyboard

## Switch positions

## Commands run
- `python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235`
- `python scripts\board_gpio_smoke_test.py --start-server --port 1239`

## COM3 observations

## Ethernet observations

## HPI observations

## Beagle 12 observations

- Reset observed: Yes
- SOF observed: Yes
- SETUP observed: Yes
- Enumeration observed: Yes (Dell Keyboard string descriptor captured successfully)
- BAD_SYNC: No
- Other errors: No

## AgentWebCam observations

## Conclusion
The PC Reference configuration is working perfectly. The Total Phase Beagle 12 analyzer is correctly set up, capturing valid USB enumeration traffic between the PC and the target keyboard.

## Next action
Proceed to Configuration 2: Terasic Host Demo isolation test.
