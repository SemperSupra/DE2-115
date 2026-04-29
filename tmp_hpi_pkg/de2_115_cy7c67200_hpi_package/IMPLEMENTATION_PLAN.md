# Implementation Plan for SemperSupra/DE2-115 CY7C67200 HPI Bring-up

## Work graph

```text
A. Preserve Ethernet baseline
B. Rename misleading ISP1761 names
C. Add CY7C67200 register/HPI/LCP/SCAN modules
D. Add host SCAN decode/wrap tools
E. Add HPI fake-target simulation model
F. Add staged CY bring-up firmware mode
G. Add reset/errata cleanup
H. Re-run board tests
I. Only then resume LCP/SIE/HID work
```

Dependencies:

```text
A -> B
A -> C
C -> F
C -> G
D -> F
E -> C/F validation
F/G -> H
H -> I
```

## Acceptance gates

Before any HPI/USB change:

```powershell
python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235
```

After each HPI/USB change:

```powershell
python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235
python scripts\board_gpio_smoke_test.py --start-server --port 1239
```

## Stage ladder for firmware

Firmware must print stage lines in this order and stop on first failure:

```text
CY_STAGE0_FPGA_HPI_BRIDGE_START
CY_STAGE0_FPGA_HPI_BRIDGE_PASS
CY_STAGE1_RESET_RELEASE_START
CY_STAGE1_RESET_RELEASE_PASS
CY_STAGE2_REG_READ_START
CY_STAGE2_REG_READ_PASS hwrev=.... cpu=.... pwr=....
CY_STAGE3_RAM_RW_START
CY_STAGE3_RAM_RW_PASS addr=1000 value=1234
CY_STAGE4_ERRATA_CLEANUP_START
CY_STAGE4_ERRATA_CLEANUP_DONE sie1msg=.... sie2msg=....
CY_STAGE5_SCAN_COPY_START
CY_STAGE5_SCAN_COPY_PASS records=... bytes=...
CY_STAGE6_LCP_CALL_START
CY_STAGE6_LCP_CALL_PASS ack=0FED
CY_STAGE7_BIOS_INT_START
CY_STAGE7_BIOS_INT_PASS
```

Do not run LCP/SIE/HID code when stage 2 or 3 fails.

## Deliverables in this package

Overlay files:

```text
docs/cy7c67200/README.md
docs/cy7c67200/memory-map.md
docs/cy7c67200/scan-format.md
docs/cy7c67200/hpi-lcp.md
docs/cy7c67200/errata-checklist.md
firmware/src/cy7c67200_regs.h
firmware/src/cy7c67200_hpi.h
firmware/src/cy7c67200_hpi.c
firmware/src/cy7c67200_lcp.h
firmware/src/cy7c67200_lcp.c
firmware/src/cy7c67200_scan.h
firmware/src/cy7c67200_scan.c
firmware/src/cy7c67200_bringup.h
firmware/src/cy7c67200_bringup.c
scripts/cy16_scan_decode.py
scripts/cy16_scanwrap.py
sim/cy7c67200_hpi_model.v
sim/cy7c67200_hpi_model_tb.v
sim/README.md
```

## Agent integration checklist

1. Copy overlay files into repo.
2. Wire new `.c` files into the firmware build system.
3. Move current inline HPI/LCP/SCAN code from `firmware/src/main.c` into the new modules.
4. Keep existing `pcd_asm.h`, `lcp_blob.h`, and `de2_bios` assets.
5. Add a compile-time or runtime option to run the staged CY bring-up before normal USB code.
6. Rename misleading `isp1761.py` / `ISP1761Bridge` to CY7C67200-specific names, preserving compatibility aliases if needed.
7. Add host tool tests for `scripts/cy16_scan_decode.py` and `scripts/cy16_scanwrap.py`.
8. Add simulation target for fake HPI target if the current test framework supports Icarus/Verilator.
9. Run Ethernet regression before/after each change.
10. Commit in small steps.
