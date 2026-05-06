# CY7C67200 Strap and Clock Checklist

Date: 2026-05-06

This checklist is the next USB/HPI step after the no-analyzer HPI ladder. It
focuses on board-level facts that the Cyclone IV fabric cannot currently
observe or force.

## Why This Is Next

The FPGA-side evidence is now strong:

- HPI writes are visible at the HPI DATA pins.
- HPI DATA reads are issued with `CS_N=0`, `RD_N=0`, `WR_N=1`, reset released,
  and the FPGA not driving the DATA bus.
- Weak pull-ups prove idle/released and reset-low DATA can sample high.
- Active HPI DATA/MAILBOX/STATUS reads still sample `0x0000`.
- Reset release changes `INT0` from low to high, proving reset has an
  observable CY-side effect.
- All 24 logical DATA/MAILBOX/ADDRESS/STATUS address permutations failed to
  produce valid readback.

The remaining likely class is therefore board/CY mode state: `GPIO30/GPIO31`
boot straps, serial EEPROM interaction, MAX II `12MHz` clock ownership, or a
board-level DATA-bus hold during active reads.

## Local Documentation Facts

- `de2_manual.pdf` says the DE2-115 uses the CY7C67200 HPI interface and shows
  CY `XTALIN` fed by MAX II `EPM240` at `12MHz`.
- `bios_manual.pdf` says `GPIO30=0/GPIO31=0` selects HPI co-processor boot,
  while `GPIO30=1/GPIO31=1` selects standalone EEPROM boot.
- `hw_notes.pdf` says `GPIO30/GPIO31` are also EEPROM `SDA/SCL`.
- `hpi_manual.pdf` warns that those I2C lines may power up high due to
  pull-ups in Cypress examples, selecting standalone/EEPROM behavior unless the
  board actively straps them otherwise.
- The current LiteX platform exposes HPI DATA/ADDR/CS/RD/WR/RST plus the known
  and experimental sidebands, but not `GPIO30`, `GPIO31`, or the CY clock.

## Checks

1. Confirm whether the DE2-115 schematic or board files show CY
   `GPIO30/GPIO31` tied low, tied high, connected to EEPROM only, or driven by
   MAX II.

   Interpretation:
   - Both low at reset supports HPI co-processor mode.
   - Both high at reset supports standalone/EEPROM mode, which would explain
     why HPI mailbox/status behavior does not look BIOS-responsive.
   - MAX II-driven straps mean the next debug target is the MAX II image/state,
     not the Cyclone IV bitstream.

2. Confirm CY `XTALIN` has a live `12MHz` clock from MAX II while CY reset is
   released.

   Interpretation:
   - No clock or wrong frequency makes HPI readback unreliable regardless of
     FPGA HPI timing.
   - A valid `12MHz` clock keeps focus on boot straps or bus-level behavior.

3. Confirm whether the serial EEPROM on CY `GPIO30/GPIO31` is populated and
   whether it can pull the strap pins high at reset.

   Interpretation:
   - Populated EEPROM plus high straps means CY may boot standalone scan code
     instead of waiting for HPI LCP.
   - No EEPROM or forced low straps makes standalone boot less likely.

4. Confirm no board-level device besides the CY can actively drive
   `OTG_DATA[15:0]` low during active HPI reads.

   Interpretation:
   - A second driver or buffer direction issue would match the weak-pullup
     contrast: idle high, active read low.
   - If CY is the only active driver, then the CY is intentionally returning
     zero or is not in the expected HPI-readable state.

## Rerun After Any Hardware/Strap Change

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_hpi_no_analyzer_contrast.ps1 -SkipEthernetGate
powershell -ExecutionPolicy Bypass -File .\scripts\run_hpi_reset_release_live_sideband_watch.ps1 -SkipEthernetGate -PreReleaseMs 4000
python scripts\hpi_address_permutation_probe.py --start-server --port 1235 --reset-each
```

If reads become nonzero, reprogram the normal root image (`0x033328D9`) before
resuming LCP/SIE/USB packet work. The currently programmed image is the
weak-pullup diagnostic (`0x03332BFF`).
