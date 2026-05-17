# Run Notes

## Goal
Terasic USB host demo with Windows-native Nios loader

## Hardware topology
PC host -> Beagle 12 -> simple USB mouse

## Switch positions

## Commands run
- `C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_pgm.exe -m jtag -o "p;DE2_115_demonstrations\DE2_115_NIOS_HOST_MOUSE_VGA\DE2_115_NIOS_HOST_MOUSE_VGA.sof"`
- `C:\intelFPGA_lite\22.1std\nios2eds\bin\gnu\H-x86_64-mingw32\bin\nios2-elf-objcopy.exe -O srec ...DE2_115_NIOS_HOST_MOUSE_VGA.elf artifacts\terasic_host_demo\DE2_115_NIOS_HOST_MOUSE_VGA.srec`
- `C:\intelFPGA_lite\22.1std\quartus\bin64\nios2-gdb-server.exe -c "USB-Blaster [USB-0]" -d 1 -i 0 --accept-bad-sysid -r -g artifacts\terasic_host_demo\DE2_115_NIOS_HOST_MOUSE_VGA.srec`
- `C:\intelFPGA_lite\22.1std\quartus\bin64\nios2-terminal.exe -c "USB-Blaster [USB-0]" -d 1 -i 0 --flush --quit-after=20`
- `python scripts\capture_beagle_events.py 200`

## COM3 observations
Not used. This run used JTAG UART through `nios2-terminal`.

## Ethernet observations
Not applicable while the Terasic reference SOF was loaded.

## HPI observations
The Terasic Nios application downloaded 80 KiB, verified OK, and started at
`0x000001B4` through Windows-native `nios2-gdb-server.exe`.

## Beagle 12 observations

- Reset observed: yes, `TGT_DISCON; RESET`
- SOF observed: no
- SETUP observed: no
- Enumeration observed: no
- BAD_SYNC: no
- Other errors: capture ended with `error=-7 OK` after connect/reset events

## AgentWebCam observations

## Conclusion
The host-side loader problem is solved without WSL, but the Terasic reference
demo remains packet-silent in this setup. Next variable is physical USB
host-power/topology/jumper/VBUS, not the Nios download path.

## Next action
Repeat with explicit downstream device/topology observations and, if possible,
a directly attached simple USB mouse on the DE2-115 HOST port.
