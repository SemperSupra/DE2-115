# Research Findings: Applying CY16 / CY7C67200 Knowledge to SemperSupra/DE2-115

Date: 2026-04-27  
Target repo: `SemperSupra/DE2-115`

## Executive conclusion

The DE2-115 project should treat the current USB problem as a **CY7C67200 Host Processor Interface (HPI) electrical/protocol bring-up problem**, not as a HID, KVM2USB, SIE, or class-driver problem. The project already has a working LiteX/VexRiscv control plane with UART, Ethernet, Etherbone, and host diagnostics. The immediate blocker is that HPI writes appear to reach the FPGA pins, but CY7C67200-originated reads still return `0x0000`.

The Cypress documents and source artifacts provide enough information to formalize the HPI, SCAN, LCP, BIOS, and errata handling into distinct project layers.

## 1. CY16 memory and BIOS context

The BIOS manual defines a practical CY16 memory map, including hardware/software vectors at low memory, the HPI interrupt/mailbox region around `0x0140-0x0148`, LCP command processor variables around `0x014A-0x01FF`, USB registers around `0x0200-0x02FF`, BIOS stack around `0x0310-0x03FF`, user code/data internal RAM beginning at `0x04A4`, memory-mapped control registers at `0xC000-0xC0FF`, and BIOS ROM at `0xE000-0xFFFF`. This directly supports adding `docs/cy7c67200/memory-map.md` and codifying the addresses already scattered in firmware. fileciteturn6file15

The BIOS reset sequence is also directly relevant: on reset, the BIOS sets the speed control register, sets PC to `0xFF00`, jumps to BIOS ROM at `0xE000`, sets `r15` to `0x0400`, initializes vectors, initializes LCP/USB idle tasks, performs boot control, processes SCAN if present, and then enters idle tasks. This means DE2-115 firmware should allow adequate post-reset delay before HPI/LCP assumptions and should distinguish "chip held/reset" from "BIOS initialized." fileciteturn6file5

## 2. SCAN record format and why it matters

The BIOS manual documents the SCAN signature structure used by `SCAN_INT`: `dw 0xC3B6`, `dw Length`, `db OpCode`, followed by opcode-specific data. It documents opcodes including write data (`0x00`), jump absolute (`0x04`), call absolute (`0x05`), and call interrupt (`0x06`). fileciteturn6file12

The CY16 Binary Utilities Reference confirms that `SCANWRAP` wraps raw binaries so the BIOS can copy them into memory and execute them. It also warns that the SCANWRAP base address must match the linker script because SCANWRAP does not relocate code. fileciteturn6file9

The supplied `scanwrap.c` confirms the actual host utility interface and opcode constants: `OPCODE_COPY = 0`, `OPCODE_JUMP = 4`, and `OPCODE_CALL = 5`. It also explains the important word-alignment workaround: SCAN data must be word-aligned, and the opcode byte otherwise misaligns the data field, so the Cypress tool inserts an initial header to align the next data block. fileciteturn7file0

## 3. HPI mailbox/status behavior

The CY7C67200 datasheet documents the HPI mailbox/status behavior. The mailbox is the common message register between the external host and CY7C67200; CY7C67200 writes to the mailbox assert `HPI_INTR`, and `HPI_INTR` deasserts when the external host reads the mailbox. The HPI status port exposes mailbox status and SIE status bits, and polling the status port does not cause a CPU HPI memory access cycle. fileciteturn6file14

This supports a strict HPI ladder: reset and basic register reads; RAM write/read; mailbox/status validation; SCAN COPY; LCP CALL/JUMP; BIOS software interrupts; SIE initialization.

## 4. Errata that must be encoded in reset/bring-up

The CY7C67200 errata requires several handling rules: VBUS-valid interrupt needs software debounce; SIE interrupt-enable bits are coupled, so global SIE interrupt bits cannot independently disable SIE1/SIE2; and SIE1msg/SIE2msg at `0x0144` and `0x0148` are uninitialized at power-up in HPI coprocessor mode and should be cleared shortly after `nRESET` deasserts, generally after about 10 ms. fileciteturn7file2

The DE2-115 firmware already references `0x0144`; it should also define `0x0148` and perform an explicit errata cleanup stage after reset release.

## 5. BIOS idle-task dependency

The Binary Utilities Reference states that USB-based QT utilities rely on the EZ-OTG/EZ-Host BIOS and require `BIOS Idle_Task` to be running; custom user code must not override it if those utilities are to work. fileciteturn6file9

The BIOS manual also explains that the BIOS runs background UART/USB idle tasks that continuously scan for the SCAN signature `0xC3B6`; chip-access utilities and debuggers use this command protocol. fileciteturn6file16

This implies two firmware styles: BIOS-cooperative mode, which preserves BIOS idle chain and uses SCAN/LCP services; and BIOS-takeover mode, which owns the chip and must replace those services. The DE2-115 project should initially stay in the BIOS-cooperative/HPI-coprocessor model.

## 6. Development environment and SCAN use in examples

The "USB Multi-Role Device Design By Example" book shows practical SCAN usage in Cypress examples. One example builds a binary, wraps it with `scanwrap se10.bin scanse10.bin 0x4a4`, and programs EEPROM with `qtui2c`. fileciteturn6file11

Another example uses scan records to modify or augment BIOS behavior and then programs EEPROM with `qtui2c eeprom.bin f`. fileciteturn6file18

This supports implementing host SCAN decode/wrap tools, HPI host-parsed SCAN execution, and later CY16 toolchain build integration.

## 7. Practical implications for DE2-115

The existing repo should add:

- A CY7C67200 HPI subsystem instead of keeping everything in `main.c`.
- A SCAN parser/decoder in both host tools and firmware.
- LCP constants and helpers in a dedicated module.
- A reset-stage errata cleanup.
- A fake HPI target simulation model to test the Wishbone bridge without hardware.
- A staged firmware bring-up mode that stops at the first failed stage.

The first required proof is not "USB packets on the Beagle." It is: read a plausible CY register value, and write/read CY RAM over HPI. Only after that should the project continue to LCP, BIOS calls, SIE init, USB reset, and HID enumeration.
