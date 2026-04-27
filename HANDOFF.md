# DE2-115 Handoff - Status Update

Date: 2026-04-27
Workspace: `C:\Users\Mark\Projects\DE2-115`

## Executive Status

- **UART:** Working on COM3 at 115200 baud and used for all current board diagnostics.
- **VGA:** Working and stable enough for bring-up.
- **Ethernet:** Port 1 is now working in forced-MII low-speed mode. AUTO10/100, 100-only, and 10-only variants each passed 50/50 ping to `192.168.178.50` plus 512 Etherbone red-LED CSR write/read loops through `litex_server` on host TCP port `1235`. The current 10-only image also passed a longer 200/200 ping plus 4096 red-LED CSR loop regression.
- **GPIO/visual self-test:** The current AUTO10/100 image includes board-test
  hooks for LEDs, switches, 7-seg, and LCD. Host GPIO smoke test passed, and
  `agentwebcam` camera `1` captured board screenshots/video during the visual
  self-test. The switch pin map has been corrected; all aligned switches now
  read `0x00000000`.
- **Saved image:** The current 10-only validation `.sof` is tracked at
  `validation_images/de2_115_vga_platform_eth10_switchfix_validated_20260427.sof`
  with SHA256
  `653CBED08D4C91ABF81BCFD7B708D980828A67BBF8C49A840DA07FA2007DBE67`.
- **Preservation manifest:** `ETHERNET_BASELINE.md` now records the working
  Ethernet settings, code paths, build commands, validation results, and
  regression rule in one place.
- **Board-wide device plan:** `DEVICE_STATUS_AND_BRINGUP.md` records the
  status of each DE2-115 device and the staged strategy for remaining bring-up.
- **USB HPI:** The FPGA-side HPI bridge now decodes the USB window correctly, uses Terasic-style registered HPI control/data timing, and successfully drives write data onto the bus. The CY7C67200 still returns `0x0000` on all read attempts, including basic control registers and memory readback, so LCP/BIOS ACK still fails. Etherbone-driven reset and HPI sample-offset sweeps also returned only zeroes.
- **Current programmed board image:** Corrected 10 Mbps Ethernet validation
  image, checksum `0x033C9E9A`. It passed 50/50 ping, 512 Etherbone CSR loops,
  and board GPIO smoke test with `SWITCHES 0x00000000`.

## Changes Since Previous Handoff

- Default Ethernet port changed from 0 to 1 in `de2_115_vga_target.py`, `scripts/build_soc.sh`, and `run.bat`.
- Fixed USB Wishbone local address decode in `cy7c67200_wb_bridge.v`; LiteX supplies absolute Wishbone word addresses, so the bridge now decodes only the local low bits inside the 64 KiB USB window.
- Corrected HPI register order in firmware to match Terasic references:
  - A=0: data
  - A=1: mailbox
  - A=2: address
  - A=3: status
- Ported `CY7C67200_IF.v` to the registered Terasic HPI boundary style and routed the bridge outputs through it.
- Added USB diagnostics for write-cycle and read-cycle debug registers, CY register probes, mailbox/status reads, and command ACK failures.
- Added MDIO diagnostics for PHY16/PHY17 ID, basic status, PHY-specific status, RGMII delay register, and LiteEth in-band status.
- Added a dedicated `eth_gtx_clocks` platform resource so RGMII gigabit TX clock uses `ENET1_GTX_CLK` (`C23`) instead of the base LiteX `ENET1_TX_CLK` (`C22`) resource.
- Changed RGMII TX clocking to use the existing 90-degree PLL output (`eth_tx_ps`) and changed firmware MDIO setup to keep PHY TX internal delay off while keeping PHY RX delay on. Current PHY17 RGMII delay register after this change is `0C62`.
- Added Ethernet firmware diagnostics for LiteEth MAC RX/TX state, event pending bits, preamble errors, CRC errors, and in-band status. The firmware clears the unused software-MAC RX pending event after each diagnostic dump.
- Removed unverified USB DACK pin assignment from the custom platform resource and narrowed OTG DREQ to manual-backed `J1`; current Quartus pin report contains no `usb_otg_dack` pins.
- Added command-line source/probe debugging for `HPI0`, `ETH0`, `ETX0`, and `ARP0`; this works from elevated host Quartus STP without the GUI.
- Added forced-MII support in the custom RGMII PHY path and validated Ethernet with ping and Etherbone.
- Added low-speed Ethernet firmware selection through `DE2_ETH_SPEED_MODE`:
  default AUTO10/100, `100`, and `10`.
- Added `scripts/ethernet_low_speed_test.py` to run the repeatable low-speed
  Ethernet regression: ping, `litex_server`, LiteX identifier read, green LED
  CSR probe, and red LED CSR write/read stress.
- Added firmware board-test hooks that print a `BOARDTEST` banner and exercise
  red LEDs, green LEDs, eight 7-segment display CSRs, LCD GPIO, and optional
  SDRAM scratch testing.
- Corrected the DE2-115 switch pin map: `SW[2]` is `AC27`, `SW[3]` is `AD27`,
  and `AD28` is not a switch pin (`HSMC_CLKOUT0` in Terasic references).
- Added `scripts/board_gpio_smoke_test.py` for repeatable Etherbone GPIO smoke
  testing.
- Added `scripts/visual_board_selftest.py` for host-driven LCD text, LED/7-seg
  visual patterns, and `agentwebcam` screenshot/video capture.
- Added `scripts/capture_uart.py` for bounded UART boot-log capture.
- Added `scripts/usb_hpi_host_diag.py` for host-triggered CY7C67200 HPI
  reset/write/read diagnostics over Etherbone.
- Added `scripts/decode_hpi_probe.py` to decode the 192-bit `HPI0`
  source/probe value.
- Normalized `signaltap/usb_hpi_capture.stp` log/display names to `log_1` /
  `signal_set_1`; Quartus still compiles only the SLD hub/fabric and
  `quartus_stp` reports no `auto_signaltap_0` instance in the SOF.

## Latest Verified Board Log

Key lines from the earlier AUTO10/100 board-test image programmed on 2026-04-26 at
17:20:13, checksum `0x033CA203`:

```text
Ping statistics for 192.168.178.50:
    Packets: Sent = 50, Received = 50, Lost = 0 (0% loss)

IDENT_PREFIX 'LiteX VGA Test SoC on DE'
ETHERBONE_CSR_STRESS_OK loops=512 ...
ETHERNET_LOW_SPEED_TEST_PASS

SWITCHES 0x00000000
LEDS_R_RW_OK
LEDS_G_PROBE 0x0000005a
SEVEN_SEG_RW_OK
LCD_GPIO_RW_OK
BOARD_GPIO_SMOKE_TEST_PASS
```

Current programmed corrected 10 Mbps image, programmed on 2026-04-27 at
06:33:00, checksum `0x033C9E9A`:

```text
Ping statistics for 192.168.178.50:
    Packets: Sent = 50, Received = 50, Lost = 0 (0% loss)

IDENT_PREFIX 'LiteX VGA Test SoC on DE'
ETHERBONE_CSR_STRESS_OK loops=512 ...
ETHERNET_LOW_SPEED_TEST_PASS

SWITCHES 0x00000000
LEDS_R_RW_OK
LEDS_G_PROBE 0x0000005a
SEVEN_SEG_RW_OK
LCD_GPIO_RW_OK
BOARD_GPIO_SMOKE_TEST_PASS
```

Visual self-test artifacts from `agentwebcam` camera `1`:

```text
SCREENSHOT local_artifacts\screenshots\board_visual_selftest_20260426_172358.jpg
VIDEO local_artifacts\videos\board_visual_selftest_20260426_172358.mp4
CROP local_artifacts\screenshots\board_visual_selftest_20260426_170047_switches_red_leds_7seg.jpg
CROP local_artifacts\screenshots\board_visual_selftest_20260426_170047_lcd.jpg
CROP local_artifacts\screenshots\board_visual_selftest_20260426_170047_device_leds_connectors.jpg
```

USB evidence from the current blocker remains:

```text
ETHDBG poll inband=0000000B ...
ETHARP op=0001 sha=50:EB:F6:7F:C6:1C spa=192.168.178.27 tha=00:00:00:00:00:00 tpa=192.168.178.50
HPI CFG: 000208FD
CY rev=0000 cpu=0000 pwr=0000 mb=0000 st=0000
HPI DBG WR cfg=000208FF ctrl=03601000 sample=00001234 cy=00001234
HPI DBG RD cfg=000208FF ctrl=03200800 sample=00000000 cy=00000000
MEM CHECK: 0000 FAIL
LCP...
FAIL
SIE1_INIT NOACK mb=0000 st=0000
USB_RESET NOACK mb=0000 st=0000
```

Host-triggered HPI diagnostic over Etherbone:

```text
HPI_HOST_CFG 0x000208ff
HPI_HOST_AFTER_WRITE cfg=0x000208ff ctrl=0x03200e00 sample=0x0000 cy=0x0000
HPI_HOST_AFTER_READ cfg=0x000208ff ctrl=0x03200e00 sample=0x0000 cy=0x0000
HPI_HOST_RESULT addr=0x1000 wrote=0x1234 read=0x0000 status=0x0000 mailbox=0x0000
HPI_HOST_MEM_RW_FAIL
```

Command-line HPI source/probe during a DATA read showed:

```text
Reset/sideband: rst=0 hpi_rst_n=1 int0=1 int1=1 dreq=0 cy_o_int=1
HPI pins: cs_n=0 rd_n=0 wr_n=1 addr=0 data=0000
Data: read=0000 sample=0000 last_sample=0000 cy_o=0000
```

Interpretation:

- USB writes are electrically visible at the FPGA HPI data pins (`0x1234` during the write cycle).
- USB reads are not returning CY7C67200-driven data; the sampled bus remains zero.
- Ethernet has moved past pinout/link detection and is usable for ping and Etherbone CSR transactions in AUTO10/100, 100-only, and 10-only low-speed modes.
- Beagle USB 12 inline capture on the DE2-115 USB HOST path sees target
  connect/disconnect/reset events but no USB packets. Passive captures with both
  this image and the Terasic USB host demo produced no SOF/SETUP/IN/OUT traffic
  on the DE2 host path.
- Active Beagle capture on 2026-04-27 with the KVM2USB inline produced 50
  events over roughly 73 seconds on the project image: repeated
  `TGT_CONNECT/UNRST` followed by `TGT_DISCON; RESET`, with no SOF/SETUP/IN/OUT
  packets. Repeating the same capture after programming Terasic's
  `DE2_115_NIOS_HOST_MOUSE_VGA.sof` produced the same no-packet pattern. This
  makes the immediate question physical/device-path compatibility, not just our
  HPI firmware.
- KVM2USB direct-to-PC validation through a USB hub succeeded at the Windows
  device level: `KVM2USB 3.0`, `KVM2USB 3.0 Config`, `VID_2B77&PID_3661`
  composite, and related HID/vendor-defined interfaces all report `OK`. A
  Beagle reference trace in the PC-hub path shows `SETUP`, descriptor `DATA`,
  `ACK`, and `IN/NAK` polling, proving the analyzer and KVM2USB can produce
  packet-level traffic. That inline reference still resets repeatedly, so do not
  treat it as a stable long-run KVM2USB trace.
- Device-mode isolation with Terasic's `DE2_115_USB_DEVICE_LED.sof` now points
  at a lower-level DE2/CY/physical USB issue, not just LiteX firmware. With the
  DE2 DEVICE Type-B path connected through the Beagle to a PC hub and KVM2USB
  unplugged from the DE2 HOST port, Beagle sees `TGT_CONNECT/UNRST` followed by
  continuous `BAD_SYNC` events and no valid USB packets. Reprogramming the
  Terasic device demo did not change the trace. Windows previously showed
  `Unknown USB Device (Device Descriptor Request Failed)` on one hub, but after
  the clean Beagle capture no DE2/unknown device is present.

## Verified Build Commands

```powershell
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_firmware.sh'
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_soc.sh 1'
```

Speed-specific firmware builds:

```powershell
docker compose exec -T litex_builder /bin/bash -lc 'FIRMWARE_CFLAGS=-DDE2_ETH_SPEED_MODE=100 /workspace/scripts/build_firmware.sh'
docker compose exec -T litex_builder /bin/bash -lc 'FIRMWARE_CFLAGS=-DDE2_ETH_SPEED_MODE=10 /workspace/scripts/build_firmware.sh'
```

```powershell
C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_sh.exe --flow compile de2_115_vga_platform
```

Run Quartus from:

```powershell
C:\Users\Mark\Projects\DE2-115\build\terasic_de2_115\gateware
```

Program:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\load_bitstream.ps1
```

Ethernet regression:

```powershell
python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235
```

Board GPIO smoke test:

```powershell
python scripts\board_gpio_smoke_test.py --start-server --port 1239
```

Visual self-test capture through the physical board camera:

```powershell
python scripts\visual_board_selftest.py --start-server --port 1238 --camera 1 --capture-backend agentwebcam --duration 10 --state-seconds 2 --hold 1 --width 1920 --height 1080 --fps 15
```

## Remaining Work

1. Keep `scripts/ethernet_low_speed_test.py` as the acceptance gate before/after USB changes. Current programmed image is the tracked corrected 10-only validation image, checksum `0x033C9E9A`, and includes the switch pin-map fix.
2. Do not trust USB debug builds until they pass the Ethernet low-speed gate. A deterministic HPI0-trigger RTL experiment changed placement enough to break Ethernet RX despite timing meeting, so preserve the validated image before further compile experiments.
3. Capture external USB HPI pins with a working SignalTap instance or an external logic analyzer during the read cycle: `OTG_DATA[15:0]`, `OTG_ADDR[1:0]`, `OTG_CS_N`, `OTG_RD_N`, `OTG_WR_N`, `OTG_RST_N`, and `OTG_INT`. The current `.stp` file is not embedding a usable capture instance.
4. Run the next Beagle capture with a simple known-good low/full-speed USB
   mouse or keyboard connected through the Beagle to the DE2-115 HOST port.
   Terasic's host mouse demo is the preferred comparison image for that test.
   If that also shows only connect/disconnect/reset and no packets, debug the
   DE2 host-port hardware/cabling/power/CY reset-clock path before more HID
   class work.
5. Before more LiteX USB firmware work, resolve the device-path `BAD_SYNC`
   symptom with Terasic's device demo: verify Beagle cable orientation, try a
   short known-good USB 2.0 Type-B cable, try direct PC port versus hub, and
   inspect the DE2 USB power/PHY/connector path. A working Terasic device demo
   is the fastest proof that the CY7C67200 physical path is sane.
6. Once USB readback works, resume LCP load verification and mailbox ACK flow.
7. Keep gigabit Ethernet deferred in the backlog; later add a separate gigabit cleanup task using `ETH0`/`ETX0` captures.
8. Use `DEVICE_STATUS_AND_BRINGUP.md` as the board-wide backlog. Start SD card
   bring-up after USB is unblocked enough to avoid losing the hardware-debug
   thread.
9. To fully validate independent transitions for all 18 switches, manually walk
   each switch and record the `switches_in` CSR value. Current evidence
   validates the all-aligned vector `0x00000000` after correcting the pin map.
