# DE2-115 USB HPI Bring-up Strategy Overlay v4

This overlay is intended to be copied into the existing `SemperSupra/DE2-115` repository.

It incorporates the current bench topology and strategy:

- DE2-115 VGA output connected to USB2KVM / KVM2USB video input.
- KVM2USB USB connection connected to the DE2-115 USB host port for later advanced host testing.
- Host COM3 connected to DE2-115 UART.
- Ethernet connected on DE2-115 Ethernet Port 1.
- Webcam/AgentWebCam available for observing board LEDs, 7-seg, LCD, switch positions, cabling, and reset/power state.
- Total Phase Beagle 12 available as packet-level USB evidence.
- USB device path has been confirmed using the Beagle 12.
- Active problem is therefore narrowed to HPI read/control behavior and/or USB host-mode/host-port path behavior, not a globally dead CY7C67200 or general USB PHY.

Recommended workflow:

1. Install docs/prompts/issues only.
2. Commit them before code changes.
3. Use `prompts/GEMINI_CLI_USB_HPI_STRATEGY_PROMPT.md` or `prompts/CODEX_CLI_USB_HPI_STRATEGY_PROMPT.md`.
4. Preserve the validated Ethernet/visual baseline.
5. Do not resume HID/KVM2USB host work until HPI readback succeeds or a Terasic host demo independently proves host traffic.
