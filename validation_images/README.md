# Validation Images

This directory stores known-good FPGA images that are intentionally tracked in
git. Build output under `build/` remains ignored; copy only images that have
clear validation value.

## `de2_115_vga_platform_eth10_switchfix_validated_20260427.sof`

- Purpose: Ethernet Port 1 forced-MII 10 Mbps validation image with the
  corrected DE2-115 switch pin map.
- Source mode: firmware built with `FIRMWARE_CFLAGS=-DDE2_ETH_SPEED_MODE=10`.
- Programmed Quartus checksum: `0x033C9E9A`.
- File SHA256: `653CBED08D4C91ABF81BCFD7B708D980828A67BBF8C49A840DA07FA2007DBE67`.
- File size: `3,554,301` bytes.
- Programmed and tested: 2026-04-27.
- Validation: 50/50 ping to `192.168.178.50`, LiteX identifier read over
  Etherbone, 512 red-LED CSR write/read loops, and board GPIO smoke test
  passed with `SWITCHES 0x00000000`.

## `de2_115_vga_platform_eth10_validated_20260426.sof`

- Purpose: Ethernet Port 1 forced-MII 10 Mbps validation image.
- Source mode: firmware built with `FIRMWARE_CFLAGS=-DDE2_ETH_SPEED_MODE=10`.
- Programmed Quartus checksum: `0x033D6EDD`.
- File SHA256: `B886FAC43010C039237CBC94BE316AEF1796E6496DE63DEAD67AFB032FB9373A`.
- File size: `3,554,300` bytes.
- Programmed and tested: 2026-04-26.
- Validation: 200/200 ping to `192.168.178.50`, LiteX identifier read over
  Etherbone, and 4096 red-LED CSR write/read loops passed.

Rebuild command:

```powershell
docker compose exec -T litex_builder /bin/bash -lc 'FIRMWARE_CFLAGS=-DDE2_ETH_SPEED_MODE=10 /workspace/scripts/build_firmware.sh'
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_soc.sh 1'
```

Compile from `build\terasic_de2_115\gateware`:

```powershell
C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_sh.exe --flow compile de2_115_vga_platform
```

Program from the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\load_bitstream.ps1
```
