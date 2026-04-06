# Project Map

## Top-Level View

### Active Source

- `de2_115_vga_platform.py`
  Purpose: Extends the LiteX DE2-115 platform with the actual pin assignments
  used by this project for VGA, LCD, USB, switches, LEDs, and 7-segment output.

- `de2_115_vga_target.py`
  Purpose: Builds the LiteX SoC, clocking, SDRAM, Ethernet, SD card, VGA
  generator, GPIO peripherals, and USB bus mapping.

- `isp1761.py`
  Purpose: Implements the Wishbone bridge to the external USB controller bus.
  Despite the filename, this is effectively a generic HPI-style bus bridge in
  the current design.

- `firmware/src/main.c`
  Purpose: Main board firmware. Handles diagnostics, LCD output, USB controller
  access, TD execution, device setup requests, and endpoint polling.

- `firmware/src/font_8x16.c`
  Purpose: Font data used by the firmware-side display logic.

### Host Automation

- `scripts/setup_host.ps1`
  Purpose: Verifies or installs host prerequisites such as Docker, Quartus, Git,
  GitHub CLI, and USB-Blaster drivers.

- `scripts/build_soc.sh`
  Purpose: Generates LiteX headers/build products and optionally reintegrates the
  firmware binary into the SoC ROM image.

- `scripts/build_firmware.sh`
  Purpose: Builds the firmware against LiteX-generated headers and libraries.

- `scripts/load_bitstream.ps1`
  Purpose: Programs the generated `.sof` file onto the DE2-115 over USB-Blaster.

### Generated Output

- `build/terasic_de2_115/`
  Purpose: LiteX-generated hardware/software output and Quartus products.
  Treat as generated unless debugging build artifacts.

- `firmware/src/demo.bin`
- `firmware/src/demo.elf`
  Purpose: Built firmware outputs consumed by the SoC build flow.

### Reference and Reverse-Engineering Material

- `DE2_115_demonstrations/`
  Purpose: Vendor demo designs. This is the most important reference tree for
  the missing CY7C67200 LCP firmware blob.

- `Downloads/`
  Purpose: Manuals, datasheets, vendor ZIPs, and extracted support tooling. This
  includes the "open system builder" reconstruction work used to derive board
  mappings.

- `tools/AgentKVM2USB/`
  Purpose: Supporting host-side investigation utilities around the KVM2USB and
  USB/HID analysis.

- `tools/AgentWebCam/`
  Purpose: Supporting utilities for webcam capture and related automation.

### Observation Artifacts

- `local_artifacts/screenshots/`
- `local_artifacts/videos/`
- `local_artifacts/logs/`
  Purpose: Bring-up evidence. These files show board state, VGA output, LCD
  output, captured sessions, and command transcripts. Useful for forensics, but
  not primary source code.

## Execution Flow

1. Host environment is prepared with `scripts/setup_host.ps1`.
2. `de2_115_vga_target.py` generates the LiteX SoC and software headers.
3. `firmware/src/main.c` is built into `demo.bin`.
4. The SoC is regenerated with `demo.bin` integrated into ROM.
5. `scripts/load_bitstream.ps1` programs the board.
6. Runtime behavior is observed through VGA, LCD, LEDs, photos, and logs.

## Hardware/Software Boundary

### FPGA Side

- Clock generation and reset handling.
- SDRAM, Ethernet, SD card integration.
- VGA timing and pixel generation.
- GPIO-mapped user interface devices.
- Bus bridge to the external USB controller.

### Firmware Side

- User-visible diagnostics.
- LCD command/data protocol.
- Controller register reads and writes.
- USB TD construction/execution.
- Device setup traffic and polling logic.

## Current Fault Line

The project is not blocked on VGA, CPU bring-up, or low-level bus access.
It is blocked between:

- Successful raw HPI communication with the CY7C67200.
- Successful higher-level USB host initialization.

The missing transition step is loading and starting the controller's LCP
firmware.

## Files To Read First

If you are resuming work, read these in order:

1. `HANDOFF.md`
2. `FINDINGS.md`
3. `de2_115_vga_target.py`
4. `firmware/src/main.c`
5. `DE2_115_demonstrations/.../lcp_data.h` referenced by `HANDOFF.md`

## Safe Editing Guidance

- Edit `de2_115_vga_platform.py`, `de2_115_vga_target.py`, and
  `firmware/src/main.c` freely when changing behavior.
- Treat `build/` as generated output.
- Treat `DE2_115_demonstrations/` and `Downloads/` as reference sources unless
  you are intentionally extracting data from them.
- Preserve `local_artifacts/` as local evidence unless you are explicitly
  cleaning artifacts.
- In this clone, `DE2_115_demonstrations/` and `tools/` are excluded via
  `.git/info/exclude` to keep normal git status focused on project-owned files.
