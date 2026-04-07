# Opportunities for Improvement and Project Comparisons

From the perspective of a potential user, this repository provides a compelling baremetal bring-up of the DE2-115 board using a LiteX SoC, VexRiscv CPU, and a raw USB OTG controller. However, there are significant opportunities for improvement in terms of architectural robustness, feature utilization, and ease of use.

## Opportunities for Improvement

### 1. Code Modularity and Naming
* **Monolithic Firmware:** Currently, `firmware/src/main.c` contains everything from LCD control, 7-segment display logic, UART, to the low-level USB TD execution and USB state machine polling. Refactoring this into modular drivers (e.g., `lcd.c`, `hex_display.c`, `cy7c67200.c`, `usb_host.c`) would vastly improve readability and maintainability.
* **Misleading Names:** The file `isp1761.py` implies support for the NXP ISP1761, but the hardware being initialized and communicated with is actually the Cypress CY7C67200. Renaming this file and class to accurately reflect the CY7C67200 will prevent confusion for future developers.

### 2. Underutilized Hardware Capabilites
* **SD Card & Ethernet:** The LiteX SoC generation in `de2_115_vga_target.py` explicitly adds an Ethernet PHY (`add_ethernet()`) and SD Card support (`add_sdcard()`). However, the baremetal firmware does not utilize these peripherals.
  * *Improvement:* Integrate a minimal embedded network stack like `lwIP` and a filesystem like `FatFS` to allow the board to load resources (like the missing USB LCP firmware blob) from an SD card or over the network.
* **VGA Framebuffer:** The current VGA implementation (`SimpleVGA`) bypasses LiteX video cores to drive a hardcoded test pattern directly via hardware counters.
  * *Improvement:* Transition to utilizing a LiteX Video Framebuffer mapped to the SDRAM. This would allow the VexRiscv firmware to draw text, diagnostics, and graphical user interfaces to the VGA output directly.

### 3. Build Automation and Cross-Platform Support
* The project relies heavily on `run.bat` and PowerShell scripts (`scripts/setup_host.ps1`), which targets a Windows environment with Docker.
  * *Improvement:* Provide a fully cross-platform Makefile, CMake, or `Justfile` to streamline the build process for Linux/macOS users who run Quartus natively or in standard Linux containers.

## Similar Projects and Capabilities to Implement

When looking at similar hardware/FPGA projects, there are several capabilities and features that could serve as inspiration for this repository:

### 1. MiSTer FPGA Project
* **Capability:** The MiSTer project (based heavily on the DE10-Nano, a close relative of the DE2-115) uses a secondary ARM processor running Linux to handle complex operations like networking, USB HID input polling, and file serving.
* **Implementation Idea:** While this project uses a baremetal RISC-V softcore, it could adopt MiSTer's **On-Screen Display (OSD)** functionality. Instead of sending raw text to the onboard LCD or serial console, diagnostic information (like USB connection state or debug logs) could be overlaid directly onto the VGA output.

### 2. TinyUSB Embedded Stack
* **Capability:** TinyUSB is a widely used, open-source cross-platform USB host/device stack.
* **Implementation Idea:** The current implementation manually creates Transaction Descriptors (TDs) and polls for hardware ACKs in `main.c`. Porting or utilizing a standardized stack like TinyUSB for the host implementation would provide out-of-the-box support for HID devices, Hubs, and Mass Storage, drastically reducing the complexity of custom USB driver code.

### 3. LiteX Ecosystem (e.g., LUNA / ValentyUSB)
* **Capability:** The broader LiteX ecosystem often utilizes pure-gateware USB implementations (like ValentyUSB or LUNA) rather than relying on external dedicated USB PHY/Controller chips.
* **Implementation Idea:** While the project's goal is board bring-up for the specific DE2-115 external Cypress chip, adding support for a gateware-based USB core on the FPGA side could serve as a reliable fallback or testing mechanism for USB HID integration if the CY7C67200 LCP firmware blob remains a blocker.
