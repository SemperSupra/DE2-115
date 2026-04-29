# One-shot Agent Prompt: Apply CY7C67200 HPI/SCAN/LCP Bring-up Package to DE2-115

You are working in the existing repository:

`https://github.com/SemperSupra/DE2-115`

The project currently has working UART, VGA, Ethernet low-speed/Etherbone, GPIO smoke tests, and a partially working CY7C67200 HPI bridge. The current blocker is that HPI writes appear on the FPGA pins, but reads from the CY7C67200 return `0x0000`, including control-register reads and RAM readback. Do not treat the current problem as a HID/KVM2USB problem yet. Treat it as a CY7C67200 HPI electrical/protocol bring-up problem.

## Critical guardrail

Preserve the working Ethernet/Etherbone baseline. Before and after every USB/HPI-impacting change, run:

```powershell
python scripts\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235
```

If Ethernet fails after your changes, stop and fix/revert before continuing. The repo history shows instrumentation can perturb placement enough to break Ethernet even when timing meets.

## Source package to apply

A package has been provided with an `overlay/` directory. Copy the overlay into the repo, then integrate it carefully:

```text
docs/cy7c67200/*
firmware/src/cy7c67200_*.h
firmware/src/cy7c67200_*.c
scripts/cy16_scan_decode.py
scripts/cy16_scanwrap.py
sim/cy7c67200_hpi_model.v
sim/cy7c67200_hpi_model_tb.v
```

The code in the overlay is intended to be complete, but you must wire the new C files into the existing firmware build system and update `main.c` to call the staged bring-up.

## Implement these changes

### 1. Rename misleading ISP1761 artifacts

The board uses Cypress CY7C67200, not NXP ISP1761. Rename where safe:

```text
isp1761.py                  -> cy7c67200_hpi.py
ISP1761Bridge               -> CY7C67200HPIBridge
```

If a broad rename would break many imports, keep a compatibility alias:

```python
ISP1761Bridge = CY7C67200HPIBridge
```

Update comments and docs so agents do not chase ISP1761 behavior.

### 2. Extract HPI/LCP/SCAN logic from `firmware/src/main.c`

Move logic into:

```text
cy7c67200_hpi.c/.h
cy7c67200_lcp.c/.h
cy7c67200_scan.c/.h
cy7c67200_bringup.c/.h
cy7c67200_regs.h
```

`main.c` should orchestrate, not contain all protocol mechanics. Keep existing code behavior, constants, and diagnostics, but centralize them.

### 3. Implement the staged bring-up gate

Add a firmware path that runs:

```c
cy_bringup_run(&ctx, CY_BRINGUP_STOP_ON_FAILURE);
```

It must print clear stage lines and stop before LCP/SIE/HID if register readback or RAM write/read fails.

Stage 2 passes only if at least one of `HW_REV_REG`, `CPU_SPEED_REG`, or `POWER_CTL_REG` is nonzero/plausible. Stage 3 passes only if writing `0x1234` to `0x1000` reads back `0x1234`.

### 4. Apply errata cleanup after reset

After releasing reset and waiting at least 10 ms, clear both SIE message registers:

```c
cy_hpi_write16(ctx, CY_SIE1MSG_REG, 0x0000); // 0x0144
cy_hpi_write16(ctx, CY_SIE2MSG_REG, 0x0000); // 0x0148
```

Log this as attempted cleanup; do not treat it as proof until HPI readback works.

### 5. Add host SCAN tools

Add:

```text
scripts/cy16_scan_decode.py
scripts/cy16_scanwrap.py
```

`cy16_scan_decode.py` must decode SCAN records:
- signature `0xC3B6`
- little-endian length
- opcode
- address where applicable
- payload length
- warnings for bad length, truncation, unknown opcode

It should be able to parse raw `.bin` and C header arrays containing bytes.

`cy16_scanwrap.py` must produce Cypress-compatible SCAN records for COPY and CALL/JUMP. It should support:

```bash
python scripts/cy16_scanwrap.py input.bin output.scan 0x04A4
python scripts/cy16_scanwrap.py input.bin output.scan 0x1000 --call-address 0x1000
```

### 6. Add HPI fake-target simulation

Add the fake target and testbench under `sim/`. If the repo has an existing simulation flow, wire it in. If not, add a README with `iverilog`/`vvp` commands.

The fake target must model:
- HPI address register,
- HPI data register with auto-increment,
- HPI mailbox,
- HPI status,
- simple 64 KiB word-addressable memory behavior.

### 7. Documentation

Add/update:

```text
docs/cy7c67200/README.md
docs/cy7c67200/memory-map.md
docs/cy7c67200/scan-format.md
docs/cy7c67200/hpi-lcp.md
docs/cy7c67200/errata-checklist.md
```

Document that USB work must not proceed past HPI stage failures.

### 8. Build and validation

Run at least:

```powershell
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_firmware.sh'
docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_soc.sh 1'
```

If possible, run Quartus compile and board validation as currently documented in `HANDOFF.md`.

At minimum, ensure the firmware compiles after the module extraction.

## Acceptance criteria

- New modules compile.
- Existing Ethernet regression remains passing.
- `main.c` is smaller and delegates CY7C67200 protocol work.
- The staged CY bring-up path stops before LCP/SIE/HID if HPI readback fails.
- `scripts/cy16_scan_decode.py` works on current SCAN blob assets.
- `scripts/cy16_scanwrap.py` can wrap a small raw binary and the decoder reads it back.
- Docs clearly state the current blocker and the stage ladder.
- No misleading ISP1761 naming remains except compatibility aliases.

## Do not do

- Do not rewrite Ethernet.
- Do not resume KVM2USB HID enumeration until CY register readback and RAM readback pass.
- Do not delete working validation images.
- Do not add SignalTap/debug RTL that breaks Ethernet without clearly gating it and preserving the known-good image.
- Do not import restrictive Cypress source directly into public code unless licensing is explicitly handled. Prefer clean-room implementations based on observed formats and public documentation.
