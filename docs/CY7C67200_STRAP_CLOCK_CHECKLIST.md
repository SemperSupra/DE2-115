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

The remaining likely class is therefore board/CY mode state: MAX II `12MHz`
clock ownership, CY/USB power and reset health, or a board-level DATA-bus hold
during active reads. The CY boot strap was checked against the Rev D schematic
after this checklist was created and is now documented as default HPI mode.

## Local Documentation Facts

- `de2_manual.pdf` says the DE2-115 uses the CY7C67200 HPI interface and shows
  CY `XTALIN` fed by MAX II `EPM240` at `12MHz`.
- `bios_manual.pdf` says `GPIO30=0/GPIO31=0` selects HPI co-processor boot,
  while `GPIO30=1/GPIO31=1` selects standalone EEPROM boot.
- `hw_notes.pdf` says `GPIO30/GPIO31` are also EEPROM `SDA/SCL`.
- `hpi_manual.pdf` warns that those I2C lines may power up high due to
  pull-ups in Cypress examples, selecting standalone/EEPROM behavior unless the
  board actively straps them otherwise.
- The DE2-115 Rev D schematic sheet 20 shows the board actively straps
  `SCL/GPIO31` and `SDA/GPIO30` low with fitted `10K` pulldowns (`R253`,
  `R254`), leaves the corresponding `10K` pullups unpopulated (`R251`, `R252`
  marked `DNI`), and labels this as `Default Setting: HPI mode`.
- The local SystemCD copy is
  `Downloads\DE2-115_v.3.0.6_SystemCD\DE2_115_schematic\de2-115_mb.pdf`
  with SHA256
  `C903D313EBA4E1DB54EF233943FBBB5DBB4F715C26F629F92EE7204C9CDC2E16`.
- The local SystemCD pin CSV agrees with the schematic/manual USB HPI pin map.
  The extracted Python System Builder metadata does not; do not use its USB
  entry as an authority for HPI pins.
- The current LiteX platform exposes HPI DATA/ADDR/CS/RD/WR/RST plus the known
  and experimental sidebands, but not `GPIO30`, `GPIO31`, or the CY clock.

## Checks

1. Confirm actual resistor population on this physical board matches the Rev D
   schematic default: `R253/R254` fitted and `R251/R252` not fitted.

   Interpretation:
   - If it matches, HPI co-processor boot straps are probably not the blocker.
   - If the pullups are fitted or pulldowns missing on this board, standalone
     EEPROM mode becomes plausible again.

2. Confirm CY `XTALIN` has a live `12MHz` clock from MAX II while CY reset is
   released.

   Interpretation:
   - No clock or wrong frequency makes HPI readback unreliable regardless of
     FPGA HPI timing.
   - A valid `12MHz` clock keeps focus on boot straps or bus-level behavior.

3. Confirm CY/USB power and reset health around the CY7C67200.

   Interpretation:
   - Reset is known to affect `INT0`, but a brownout, missing VCC rail, or
     missing `USB_12MHz` can still leave HPI reads stuck at zero.
   - The schematic shows `USB_12MHz` entering `XTALIN`; the Cyclone IV cannot
     generate or observe that node in the current design.

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
