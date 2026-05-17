# Handoff Report: 2026-05-17 (Board-A HPI Confirmation)

## Current Status
- **Board Life:** **RESTORED on board A with candidate pad-capture image**. Board
  B was swapped out, board A was swapped in, and board A is programmed with
  checksum `0x033626D0` and pings at `192.168.178.50`.
- **Candidate image:** `artifacts\de2_115_vga_platform_hpi_pad_capture_033626D0_20260517.sof`.
- **Etherbone:** **FUNCTIONAL on candidate image**.
  `scripts\ethernet_low_speed_test.py --ping-count 20 --csr-loops 128 --bind-port 1235`
  passed on board A and read identifier prefix `LiteX VGA Test SoC on DE`.
- **UART:** **FUNCTIONAL**. BIOS heartbeat logs are visible on COM3 at 115200 baud.
- **USB HPI Debug:** **Rung 1 still failed**.
    - Fast canonical probe (`ACCESS_CYCLES=6`) returns all `0x0000`.
    - Fast index-15 / `legacy-data2-addr3` probe returns stable `0xf2f2`,
      not the written RAM words, so it is alias evidence rather than a pass.
    - HPI0 source/probe canonical read capture confirms the bridge asserts a
      real read cycle (`addr=0`, `CS_N=0`, `RD_N=0`, `RST_N=1`) with fast
      timing, while sampled HPI data remains `0x0000`.
    - On-FPGA pad snapshot confirms canonical data write drives
      `hpi_data=0x55aa` at `addr=0`, but canonical data read samples
      `hpi_data=0x0000` at `addr=0` with `CS_N=0`, `RD_N=0`, `WR_N=1`.
    - Board A reproduced the same canonical pad snapshot as board B:
      write data is visible at the FPGA pad-facing bus, while read data remains
      `0x0000`. The legacy/index-15 alias changed to `0xcfcf`, confirming it is
      not valid memory readback.
    - Board A reset/timing sweep still failed canonical Rung 1 across `spec`,
      `fast`, and `slow` timing after a longer reset dwell (`0.5 s` low,
      `2.0 s` high). Spec and slow pad captures also sampled read data as
      `0x0000`.
- **Terasic USB Host Demo:** **Host-native loader works; demo packet-silent**.
    - Board A accepted
      `DE2_115_demonstrations\DE2_115_NIOS_HOST_MOUSE_VGA\DE2_115_NIOS_HOST_MOUSE_VGA.sof`
      over USB-Blaster.
    - `scripts\run_terasic_usb_host_demo_host.ps1` replaces the missing
      WSL-backed `nios2-download` step with a Windows-native flow:
      ELF to SREC via `nios2-elf-objcopy.exe`, then reset/download/verify/go
      through `nios2-gdb-server.exe`.
    - The loader downloaded 80 KiB, verified OK, and started the Nios CPU at
      `0x000001B4`.
    - Beagle capture
      `artifacts\usb-hpi-runs\20260517-173028\beagle12\capture_20260517-173031.txt`
      saw connect/reset state changes but no SOF or SETUP packets.
    - User confirmed actual topology:
      `DE2-115 HOST USB-A -> Beagle 12 -> USB2KVM USB-A`, with PC-side HID
      injection through AgentUSB2KVM/KVM2USB.
    - `scripts\inject_agent_kvm_hid.py` successfully sends keyboard, touch,
      and relative mouse reports to KVM2USB. Beagle capture
      `artifacts\usb-hpi-runs\20260517-180923\beagle12\capture_20260517-180935.txt`
      still showed repeated target connect/reset cycles and no SOF/SETUP.
    - Board A has been restored to the candidate pad-capture image checksum
      `0x033626D0`.

## Key Changes
- **ROM Size:** Permanently increased to 64 KiB (`0x10000`) to fit BIOS + firmware.
- **CSR Map:** Aligned firmware with the shifted CSR map.
- **Ethernet Pin Note:** Pin audit shows `ENET1_GTX_CLK` is `PIN_C23` and
  `PIN_C22` is `ENET1_TX_CLK`; do not apply the older C22 note blindly.
- **HPI Fix:** Re-applied 2-cycle address setup phase in the bridge.
- **HPI Pad Capture:** Added on-FPGA 64-bit pad snapshots for canonical address
  write, data write, and data read.
- **CI Delegation:** Added manual workflow dispatch and fixed stale CI gates.
  Static Checks and LiteX SoC Build both pass under manual dispatch.

## Next Steps for Codex CLI
1.  **Jules feedback:** Jules session `3912795874550261687` completed. It
    proposed a one-cycle HPI strobe-delay patch and reinforced reset/strap/VBUS
    audit tasks. Do not apply the RTL patch as-is: it only touched the mirrored
    `rtl/` bridge and is stale relative to the active root bridge, which already
    uses explicit strobe gating and has board evidence. Earlier pad-capture
    review session `14997796971249417694` still had no completed status in the
    CLI.
2.  **Terasic demo or protocol review:** Second-board confirmation is complete:
    board A matches board B at the canonical readback failure. The next useful
    boundary is no longer the ELF download path or HID injection path; it is
    physical USB host-power, jumper/VBUS, and CY7C67200 board-level conditions
    because the Terasic reference design now runs and AgentUSB2KVM injects
    reports, but the bus remains packet-silent.
3.  **Do not run LCP:** Rung 1 canonical memory write/read is not proven.
4.  **Board swaps:** Four DE2-115 boards are available. Swap only after the
    same candidate SOF has a clear pass/fail on the first board.
5.  **Delegation boundary:** GitHub Actions can run Static Checks and LiteX SoC
    Build; Jules can review docs/RTL/scripts; Docker can build LiteX/SoC;
    Quartus programming, Ethernet, HPI captures, and Terasic demo observations
    remain local-only.

## Environment
- **Branch:** `ethernet-baseline-shim`
- **Live image on board A:** `artifacts\de2_115_vga_platform_hpi_pad_capture_033626D0_20260517.sof`
- **Port:** `litex_server` target UDP 1234; host bind port 1235 for tests.
- **UART:** COM3, 115200.
- **Latest checkpoints:** `5426c17` records board-A confirmation; `372a84e`
  records the reset/timing sweep; `bc6510e` documents the active
  schematic/strap/VBUS orchestration phase. Commit `24cbb11` records the
  earlier container blocker; the current update records the host-native fix.
