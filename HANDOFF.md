# DE2-115 Handoff - VGA & USB HID Project

## Current Status
* **Repository:** Local git repo is initialized and pushed to `git@github.com:SemperSupra/DE2-115.git` on branch `main`.
* **Automation:** `run.bat` now completes end-to-end through host checks, Docker build/up, LiteX SoC generation, firmware build, firmware ROM integration, Quartus compile, and USB-Blaster programming.
* **Processor:** VexRiscv (RISC-V) implemented via LiteX.
* **VGA Hardware Path:** Gateware builds and programs successfully. The simple VGA generator is still the active output path in the SoC.
* **USB Hardware:** Conclusively identified as **Cypress CY7C67200** (EZ-OTG). Wishbone-to-HPI bridge is verified working via register/ROM dumps.
* **USB Driver:** Partially implemented. Firmware still hangs during the high-level Cypress initialization sequence (`Err: t1_2` on LCD) because the chip LCP firmware has not yet been loaded.
* **Post-programming observation:** AgentKVM2USB detects the Epiphan KVM2USB 3.0 device and all HID endpoints, and it can capture a 1920x1080 frame. However, its status API still reports `resolution: 0x0` and `is_signal_active: false`, so active VGA signal confirmation is still incomplete.

## Technical Findings
1. **Chip Identity:** Registers `0xC004` (0x0011), `0xC002` (0x0100), and `0xC008` (0x000F) match the CY7C67200 datasheet defaults exactly.
2. **Hang Cause:** The Cypress chip requires a proprietary firmware blob (LCP) to be loaded into its internal RAM (address `0x0000`) before it will respond to the `HUSB_SIE1_INIT_INT` (`0x0072`) command.
3. **Firmware Source:** The required firmware is located in `DE2_115_demonstrations/DE2_115_NIOS_HOST_MOUSE_VGA/software/DE2_115_NIOS_HOST_MOUSE_VGA/lcp_data.h`.
4. **Automation Fixes Completed This Session:**
   * `run.bat` logging was fixed so `build.log` is readable.
   * `docker-compose.yml` had the obsolete `version` key removed.
   * `run.bat` Quartus invocation was fixed; the failure was invalid `cmd.exe` quoting around `quartus_sh.exe`.
5. **Tool Status:** Nested tool repos under `tools/` were synced to upstream `origin/main`. `AgentKVM2USB` still has one preserved local stash (`pre-sync local test_sdk.py adjustment`), but the working tree is clean.

## Progress
- [x] Corrected VGA pin assignments and DAC timing.
- [x] Corrected USB Data/Address pin mappings for CY7C67200.
- [x] Verified HPI bus communication with VexRiscv.
- [x] Implemented basic TD (Transaction Descriptor) execution engine in C.
- [x] Added diagnostic LCD output for USB status codes.
- [x] Fixed the top-level automation so `run.bat` completes through bitstream deployment.
- [x] Captured post-deployment observations using AgentKVM2USB and AgentWebCam.

## Observation Artifacts
- `local_artifacts/observations/agentkvm2usb/kvm_capture.jpg`
- `local_artifacts/observations/agentkvm2usb/kvm_observation.json`
- `local_artifacts/observations/agentwebcam/board_observation.jpg`
- `local_artifacts/observations/agentwebcam/webcam_observation.json`

## Remaining Open Questions
1. Does `kvm_capture.jpg` show the expected VGA test pattern, or is the KVM capture path showing a blank/other input despite successful FPGA programming?
2. Is the KVM status path (`resolution 0x0`, inactive signal) wrong, or is the board not yet driving a stable monitor-recognizable VGA output after programming?
3. What does the board LCD / LED state show immediately after programming and after a manual board reset?
4. Does the serial console provide additional runtime evidence after programming and reset?

## Next Steps
1. **Inspect the deployed board state:**
   * Review `kvm_capture.jpg` for actual VGA content.
   * Review `board_observation.jpg` for LEDs/LCD/reset state.
   * If needed, capture another observation immediately after pressing board RESET.
2. **Use serial console:**
   * Connect at 115200 baud.
   * Reset the board after programming and record boot / firmware output.
3. **Resume Cypress USB bring-up:**
   * Extract the LCP blob from `lcp_data.h`.
   * Add an HPI RAM loader in `firmware/src/main.c`.
   * Boot the LCP firmware and retry `HUSB_SIE1_INIT_INT`.
4. **Verify end-to-end USB/KVM behavior:**
   * Once LCP is running, retry enumeration.
   * Re-check AgentKVM2USB status resolution / signal-active state.
   * Use the endpoint polling loop to confirm HID activity.
