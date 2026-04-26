# SignalTap Debugging Strategy for DE2-115 Bring-Up

This project now has enough firmware-side evidence to make the next USB debug step hardware-specific. UART, Etherbone, and internal bridge debug prove that USB HPI writes are reaching the FPGA-side bus, while every CY7C67200 read still samples `0x0000`. Ethernet Port 1 is working in the forced-MII low-speed path; AUTO10/100, 100-only, and 10-only variants pass ping and Etherbone CSR stress.

## Current Debugging Infrastructure

- **UART:** Primary status channel on COM3 at 115200 baud.
- **LiteScope:** `hpi_analyzer` and `eth_analyzer` are instantiated for higher-level SoC capture.
- **ISSP/altsource_probe:** Present for `HPI0`, `ETH0`, `ETX0`, and `ARP0`; command-line STP reads work from elevated host PowerShell.
- **Quartus-native debug:** Preferred for external pin truth because Quartus runs on the Windows host with direct USB-Blaster access.
- **Capture files:** `signaltap/usb_hpi_capture.stp` and `signaltap/eth_rgmii_capture.stp` are the current repo-tracked sessions. Run them with elevated `quartus_stp.exe` on the host, not inside Docker.

## Debug Priorities

### 1. USB HPI Readback

Current evidence:

```text
HPI DBG WR ... sample=00001234 cy=00001234
HPI DBG RD ... sample=00000000 cy=00000000
HPI0 read_data: rst=0 hpi_rst_n=1 cs_n=0 rd_n=0 wr_n=1 addr=0 data=0000
Beagle USB 12: TGT_CONNECT/TGT_DISCON/RESET events only, no SOF/SETUP packets
```

Interpretation:

- FPGA HPI write drive is working.
- FPGA HPI read cycle is being issued.
- The CY7C67200 is not returning nonzero data at the FPGA pad sample point. An Etherbone reset/sample sweep from 0 to 60 cycles also returned only zeroes, so a simple sample-offset change is unlikely to fix it.
- USB-line capture sees target presence/reset transitions but no host packets, so the CY is not reaching a functional USB-host state.

SignalTap should capture external pads, not only internal bridge state.

Signals:

- `usb_otg_data[15:0]`
- `usb_otg_addr[1:0]`
- `usb_otg_cs_n`
- `usb_otg_rd_n`
- `usb_otg_wr_n`
- `usb_otg_rst_n`
- `usb_otg_int0`
- `usb_otg_int1`
- `usb_otg_dreq`

Recommended trigger:

- Falling edge of `usb_otg_cs_n`, with qualifiers for `usb_otg_rd_n == 0` to isolate reads.
- Use a second capture for writes with `usb_otg_wr_n == 0`.

Goal:

- Confirm whether `OTG_DATA` is driven by the CY during reads.
- Confirm `RD_N`, `CS_N`, address, and reset timing at the actual pins.
- Confirm no bus contention during writes.

### 2. Ethernet Port 1 Baseline

Current evidence:

```text
INBAND=0000000B
ping 192.168.178.50: 200 sent, 200 received
ETHERBONE_CSR_STRESS_OK loops=4096
ETHERNET_LOW_SPEED_TEST_PASS
```

Interpretation:

- The previous "LiteEth in-band is zero" and "ping fails" blockers are resolved in the forced-MII low-speed path.
- AUTO10/100, 100-only, and 10-only have all passed the current regression. The current 10-only image also passed a longer 200/200 ping plus 4096 red-LED CSR loop run.
- Gigabit mode remains a backlog cleanup target, not the current blocker.

Signals:

- LiteEth MAC source/sink streams through `eth_analyzer`.
- RGMII RX/TX pads if MAC stream capture is inconclusive.

Recommended trigger:

- RX valid assertion on the MAC sink/source path.
- RGMII `rx_ctl` assertion for raw frame entry.

Goal:

- Keep `scripts/ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235` as the known-good regression test.
- Use `ETH0`/`ETX0` only when deliberately revisiting gigabit timing or investigating a low-speed regression.

### 3. VGA

VGA is not the current blocker. Only instrument if display regressions appear.

## Tooling Guidance

- Use native Quartus SignalTap/source-probe for external HPI/RGMII pin captures from the Windows host.
- Use LiteScope for Wishbone/MAC-level context once physical signaling is proven.
- Avoid simultaneous SignalTap/LiteScope/JTAGBone experiments unless the JTAG chain has been explicitly validated for that combination.
