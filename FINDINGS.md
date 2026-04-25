CPU is ALIVE and executing! The system now includes robust diagnostic firmware and LiteScope analyzers for both Ethernet and USB subsystems.

### Current Status (April 2026)
- **UART Integration**: SUCCESS (115200 baud, COM3).
- **VGA Stability**: SUCCESS (Registered sync signals).
- **USB HPI Bridge**: SUCCESS (Hardware verified, register access `0x04FE` confirmed).
- **Ethernet**: Link UP (1000Mbps), but IP communication issues persist (ARP/Ping unreachable).

### Phase Status
- **Phase 1 (Ethernet)**: Active. MDIO delay tuning and phase-shifted clock domains implemented.
- **Phase 2 (USB)**: Active. HPI timing tuned and co-processor boot sequence implemented. Currently awaiting successful handshake (`0x1000` message).
- **Phase 3 (Conformance)**: Deferred. Issue #4 created for USB-IF compliance.

### Build Workflow
1. Rebuild Firmware (Container): `docker exec litex_env /bin/bash /workspace/scripts/build_firmware.sh`
2. Regenerate SoC (Container): `docker exec litex_env /bin/bash /workspace/scripts/build_soc.sh 1`
3. Compile Bitstream (Host): `.\scripts\build_bitstream.ps1`
4. Load Bitstream (Host): `.\scripts\load_bitstream.ps1`
