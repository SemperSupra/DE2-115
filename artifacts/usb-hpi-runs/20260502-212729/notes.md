# Run Notes

## Goal
Task 1C: LiteX Host Firmware with bypassed Loopback

## Hardware topology
DE2-115 host port (LiteX Patched) -> Beagle 12 -> simple USB keyboard

## Switch positions

## Commands run
- `python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235`
- `python scripts\board_gpio_smoke_test.py --start-server --port 1239`

## COM3 observations

## Ethernet observations

## HPI observations

## Beagle 12 observations

- Reset observed: 
- SOF observed: 
- SETUP observed: 
- Enumeration observed: 
- BAD_SYNC: 
- Other errors: 

## AgentWebCam observations

## Conclusion

## Next action
