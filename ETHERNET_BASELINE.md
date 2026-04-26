# Ethernet Baseline

Date: 2026-04-26

This file is the preservation manifest for the currently working DE2-115
Ethernet configuration. Treat it as the source of truth before changing
Ethernet, USB, clocks, or PHY setup.

## Validated Scope

- Board: Terasic DE2-115.
- Active port: Ethernet Port 1.
- FPGA Ethernet path: LiteEth RGMII wrapper forced into the MII/10-100 path.
- Validated firmware modes:
  - Default `AUTO10/100`
  - `DE2_ETH_SPEED_MODE=100`
  - `DE2_ETH_SPEED_MODE=10`
- Deferred: 1 Gb RGMII. Do not mix gigabit cleanup with USB HPI debug.

## Network Settings

- Board/Etherbone IP: `192.168.178.50`
- Local LiteEth MAC IP in target: `192.168.178.51`
- Remote host IP default in target: `192.168.178.27`
- Etherbone UDP port: `1234`
- Host `litex_server` TCP bind port used for tests: `1235`

## Preserved Code Settings

- `de2_115_vga_target.py`
  - Defaults to Ethernet Port 1.
  - Instantiates `LiteEthPHYRGMII(... force_mii=True)`.
  - Uses `DE2_ETH_CORE_IP`, defaulting to `192.168.178.50`.
- `de2_115_vga_platform.py`
  - Adds `eth_gtx_clocks`.
  - Port 1 GTX clock maps to `ENET1_GTX_CLK` / pin `C23`.
- `altera_rgmii.py`
  - Adds the forced-MII/GMII mux path.
  - `force_mii=True` prevents the current working image from entering the 1 Gb path.
- `firmware/src/main.c`
  - Defines `DE2_ETH_SPEED_MODE` with default `0` for `AUTO10/100`.
  - Defines `ETH_SPEED_100_ONLY` as `100`.
  - Defines `ETH_SPEED_10_ONLY` as `10`.
  - Disables 1000BASE-T advertisement via PHY register 9.
  - Constrains PHY register 4 advertisement for AUTO10/100, 100-only, or 10-only.
  - Prints `ETHMODE=...`, PHY diagnostics, and LiteEth `INBAND`.
- `scripts/build_firmware.sh`
  - Applies `FIRMWARE_CFLAGS` to C and assembly compile rules.
- `scripts/build_soc.sh`
  - Defaults SoC generation to Ethernet Port 1.
- `scripts/ethernet_low_speed_test.py`
  - Runs ping, starts `litex_server`, reads the LiteX identifier, probes green LED CSR access, and stresses red LED CSR write/read.
  - Red LEDs are used for sustained stress because firmware owns green LEDs as a heartbeat.

## Build Commands

Default AUTO10/100:

```powershell
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_firmware.sh'
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_soc.sh 1'
```

100-only:

```powershell
docker compose exec -T litex_builder /bin/bash -lc 'FIRMWARE_CFLAGS=-DDE2_ETH_SPEED_MODE=100 /workspace/scripts/build_firmware.sh'
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_soc.sh 1'
```

10-only:

```powershell
docker compose exec -T litex_builder /bin/bash -lc 'FIRMWARE_CFLAGS=-DDE2_ETH_SPEED_MODE=10 /workspace/scripts/build_firmware.sh'
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_soc.sh 1'
```

Quartus compile from `build\terasic_de2_115\gateware`:

```powershell
C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_sh.exe --flow compile de2_115_vga_platform
```

Program from repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\load_bitstream.ps1
```

Regression test:

```powershell
python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235
```

Extended 10 Mbps regression:

```powershell
python scripts\ethernet_low_speed_test.py --ping-count 200 --csr-loops 4096 --bind-port 1235
```

## Validation Results

- AUTO10/100: Quartus compile passed, programmed checksum `0x033D7486`, 50/50 ping, 512 CSR loops passed.
- 100-only: Quartus compile passed, programmed checksum `0x033D701B`, 50/50 ping, 512 CSR loops passed.
- 10-only: Quartus compile passed, programmed checksum `0x033D6EDD`, 50/50 ping, 512 CSR loops passed.
- 10-only extended run: 200/200 ping, LiteX identifier read, 4096 red-LED CSR write/read loops passed.
- Recurring Quartus caveat: timing is met, but clock uncertainty/unconstrained warnings remain.

## Saved Validation Image

- File: `validation_images/de2_115_vga_platform_eth10_validated_20260426.sof`
- Purpose: Port 1 forced-MII 10 Mbps validation image.
- Programmed Quartus checksum: `0x033D6EDD`.
- SHA256: `B886FAC43010C039237CBC94BE316AEF1796E6496DE63DEAD67AFB032FB9373A`
- Size: `3,554,300` bytes.

## Debug Hooks Preserved

- `scripts/read_source_probe.tcl`
- `decode_eth_probe.py`
- `signaltap/eth_rgmii_capture.stp`
- `SIGNALTAP_STRATEGY.md`

Use native host Quartus tools from elevated PowerShell for source/probe or
SignalTap captures. Docker is for LiteX build work, not JTAG capture.

## Regression Rule

Before resuming USB or modifying clocks/PHY code, run:

```powershell
python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235
```

After any Ethernet-adjacent change, rerun all three low-speed firmware variants
or explicitly document why only one mode is affected.
