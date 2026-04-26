# Findings

Date: 2026-04-26

## Current Status

- **CPU/UART:** VexRiscv firmware is executing and UART diagnostics are reliable on COM3 at 115200 baud.
- **VGA:** Working.
- **Ethernet:** Port 1 is the active/default port and is working in the forced-MII low-speed path. AUTO10/100, 100-only, and 10-only variants each passed 50/50 ping to `192.168.178.50` plus 512 Etherbone red-LED CSR write/read loops through host TCP port `1235`. The current 10-only image also passed a longer 200/200 ping plus 4096 red-LED CSR loop regression.
- **GPIO/visual self-test:** The current AUTO10/100 board image includes a host-driven visual self-test path. Red LEDs, green LEDs, 7-segment display CSRs, LCD GPIO, and the current switch vector were exercised over Etherbone and captured with `agentwebcam`. The switch pin map has been corrected; all aligned switches now read `0x00000000`.
- **USB:** HPI address decode, HPI register order, write timing, and reset control have been corrected. HPI write data is visible on the bus, but CY7C67200 reads still return `0x0000`. A reset/sample-offset sweep over Etherbone also returned only zeroes.
- **Board-wide device matrix:** `DEVICE_STATUS_AND_BRINGUP.md` now records the
  current status of every DE2-115 device class and the staged bring-up plan for
  remaining peripherals.

## Evidence

Latest Ethernet board evidence after firmware, SoC, Quartus, and board programming:

```text
Ping statistics for 192.168.178.50:
    Packets: Sent = 50, Received = 50, Lost = 0 (0% loss)

IDENT_PREFIX 'LiteX VGA Test SoC on DE'
ETHERBONE_CSR_STRESS_OK loops=512 ...
ETHERNET_LOW_SPEED_TEST_PASS
```

Latest GPIO/visual evidence from the current AUTO10/100 image programmed with
checksum `0x033CA203`:

```text
IDENT_PREFIX 'LiteX VGA Test SoC on DE'
SWITCHES 0x00000000
LEDS_R_RW_OK
LEDS_G_PROBE 0x0000005a
SEVEN_SEG_RW_OK
LCD_GPIO_RW_OK
BOARD_GPIO_SMOKE_TEST_PASS

SCREENSHOT local_artifacts\screenshots\board_visual_selftest_20260426_172358.jpg
VIDEO local_artifacts\videos\board_visual_selftest_20260426_172358.mp4
SWITCHES_FINAL 0x00000000
VISUAL_BOARD_SELFTEST_CAPTURE_PASS
```

Useful extracted evidence frames/crops:

- `local_artifacts\screenshots\board_visual_selftest_20260426_172358.jpg`
- `local_artifacts\screenshots\board_visual_selftest_20260426_170047_frame_0.5s.jpg`
- `local_artifacts\screenshots\board_visual_selftest_20260426_170047_switches_red_leds_7seg.jpg`
- `local_artifacts\screenshots\board_visual_selftest_20260426_170047_lcd.jpg`
- `local_artifacts\screenshots\board_visual_selftest_20260426_170047_device_leds_connectors.jpg`

Latest USB board evidence:

```text
ETHARP op=0001 sha=50:EB:F6:7F:C6:1C spa=192.168.178.27 tha=00:00:00:00:00:00 tpa=192.168.178.50
CY rev=0000 cpu=0000 pwr=0000 mb=0000 st=0000
HPI DBG WR cfg=000208FF ctrl=03601000 sample=00001234 cy=00001234
HPI DBG RD cfg=000208FF ctrl=03200800 sample=00000000 cy=00000000
MEM CHECK: 0000 FAIL
SIE1_INIT NOACK mb=0000 st=0000
```

## USB Findings

- The original USB debug decode was wrong because LiteX presents absolute Wishbone word addresses. The bridge now decodes only local low bits inside the USB window.
- Firmware HPI register order is confirmed against Terasic sources:
  - `HPI_DATA = 0`
  - `HPI_MAILBOX = 1`
  - `HPI_ADDR = 2`
  - `HPI_STATUS = 3`
- The registered Terasic-style HPI wrapper is now used for external address/control/data pins.
- The write path is proven at the FPGA pin-sampling level: the bridge records `0x1234` on `HPI_DATA` during the write cycle.
- The read path is still blocked below the firmware protocol level: CY control registers, mailbox, status, and memory readback all return zero.
- Command-line source/probe captures show reset released and valid read cycles:
  `CS_N=0`, `RD_N=0`, `WR_N=1`, `ADDR=0`, `HPI_RST_N=1`, but `HPI_DATA=0000`.
- A host-driven Etherbone sweep held CY reset low, released it, and sampled with
  offsets from 0 to 60 cycles. DATA, STATUS, MAILBOX, and bridge debug sample
  registers stayed `0x0000` for every point.
- Total Phase Beagle USB 12 inline capture on the DE2-115 USB HOST Type-A path
  sees downstream target connect/disconnect/reset events, including during FPGA
  reprogramming, but no SOF/SETUP/IN/OUT packets. This confirms USB D+/D-
  wiring/analyzer placement is seeing the device side, but the CY7C67200 is not
  reaching initialized host traffic.

## Ethernet Findings

- Port 1 is the correct current target for the connected PHY path.
- The base LiteX DE2-115 `eth_clocks:1.tx` resource maps to `C22` (`ENET1_TX_CLK`), which is not the gigabit GTX clock. The project now uses a custom `eth_gtx_clocks:1.tx` resource mapped to `C23` (`ENET1_GTX_CLK`).
- PHY17 responds to MDIO; PHY16 reads all ones and should be treated as absent/floating for this setup.
- LiteEth in-band status now reports forced 10/100 link (`INBAND=0000000B`) in the working image.
- ICMP ping works and Etherbone CSR access works through `litex_server --udp --udp-ip 192.168.178.50` when the host TCP bind port is not already occupied. Port `1235` was used for the successful test.
- The stable path uses the added MII/GMII mux with forced MII for Port 1.
- Firmware now supports explicit low-speed modes with `DE2_ETH_SPEED_MODE`: default AUTO10/100, `100`, and `10`.
- `scripts/ethernet_low_speed_test.py` is the current regression test. It runs Windows ping, starts `litex_server`, reads the LiteX identifier, probes green LED CSR access, and stresses the red LED CSR. Green LEDs are firmware-owned heartbeat outputs, so they are not used for sustained CSR stress.
- Validation on 2026-04-26:
  - AUTO10/100: Quartus compile passed, programmed checksum `0x033D7486`, 50/50 ping, 512 CSR loops passed.
  - 100-only: Quartus compile passed, programmed checksum `0x033D701B`, 50/50 ping, 512 CSR loops passed.
  - 10-only: Quartus compile passed, programmed checksum `0x033D6EDD`, 50/50 ping, 512 CSR loops passed; extended 200/200 ping plus 4096 red-LED CSR loops passed after removing the firmware-owned green LED from the sustained stress loop.
- Gigabit RGMII remains a deferred backlog item. Do not use it as part of the current USB recovery path.

## GPIO and Visual Self-Test Findings

- `scripts/board_gpio_smoke_test.py` now provides a repeatable Etherbone smoke
  test for identifier readback, current switch vector, red LED CSR write/read,
  green LED probe, all eight 7-segment output CSRs, and LCD GPIO output.
- `scripts/visual_board_selftest.py` can drive LCD text, LED patterns, and
  7-segment patterns while capturing evidence through `agentwebcam`. Camera `1`
  is the physical board view in the current setup; camera `0` is not useful for
  board visual evidence.
- The LCD accepted HD44780 8-bit initialization through the raw `lcd_out` CSR
  and displayed `DE2-115 SELFTEST` with the current switch vector.
- The 7-segment displays and top LED bank visibly changed during the recorded
  self-test, though the seven-segment LEDs overexpose in still images. The
  high-resolution video is the best evidence for state changes.
- The previous `switches_in=0x00000008` result was a pin-map bug, not switch
  hardware state. The project had skipped official `SW[2]=AC27` and assigned
  `AD28` as a switch input; Terasic references use `AD28` for `HSMC_CLKOUT0`.
  The corrected map is `SW[0..17] = AB28 AC28 AC27 AD27 AB27 AC26 AD26 AB26
  AC25 AB25 AC24 AB24 AB23 AA24 AA23 AA22 Y24 Y23`.
- After rebuilding and programming the corrected image, all aligned switches
  read `0x00000000`, matching the board view. Full independent validation of
  all 18 switches still requires a manual walk of each switch while logging the
  CSR value.
- Device/connector indicator LEDs are visible in the captured board view and are
  useful for operator feedback, but their exact semantic mapping still needs a
  per-device expected-state table.

## Verified Build Status

- Firmware build: passed.
- SoC generation: passed with Ethernet Port 1.
- Quartus full compile: passed with 0 errors.
- Board programmed with the 10-only validation image on 2026-04-26 at 15:53:51, checksum `0x033D6EDD`; ping and Etherbone CSR stress tests passed after programming.
- A copy of that validation image is tracked at `validation_images/de2_115_vga_platform_eth10_validated_20260426.sof`.
- Validation image SHA256: `B886FAC43010C039237CBC94BE316AEF1796E6496DE63DEAD67AFB032FB9373A`.
- Current board image after the switch pin-map fix is the default AUTO10/100
  image with board-test firmware hooks, checksum `0x033CA203`. Post-fix
  regression on 2026-04-26 passed 50/50 ping plus 512 Etherbone CSR loops and
  `BOARD_GPIO_SMOKE_TEST_PASS`.
- Timing: met, but the design is still not fully constrained.

Known recurring Quartus warnings:

- Clock uncertainty assignments are missing.
- The previous `eth_tx_clk` PLL cross-check mismatch was eliminated by removing the fixed 125 MHz PLL TX clock from the active Ethernet path.

## Next Technical Step

Ethernet next step: keep the low-speed regression script as the acceptance gate for future changes. If the board should be left in the general-purpose network baseline rather than a speed-specific validation image, rebuild/program the default AUTO10/100 firmware before continuing USB.

For USB, do not keep changing LCP or SIE firmware until HPI readback is proven. Capture the external OTG pins during one write and one read, or compare with a known-good Terasic USB demo bitstream on the same board:

- `OTG_DATA[15:0]`
- `OTG_ADDR[1:0]`
- `OTG_CS_N`
- `OTG_RD_N`
- `OTG_WR_N`
- `OTG_RST_N`
- `OTG_INT`

For gigabit Ethernet, keep the work in the backlog until Ethernet low-speed and USB are both stable. Use `ETH0`/`ETX0` source-probe captures when that backlog item is deliberately resumed.
