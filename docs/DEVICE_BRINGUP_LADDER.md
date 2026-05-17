# Board Device Bring-up Ladder Plan
Date: 2026-05-10

## 1. Vision
Systematically climb the "hardware ladder" from verified low-level signals to high-level HID and Storage drivers, using the HPI breakthrough as the foundation.

## 2. The Ladder Steps

### Rung 1: HPI Protocol Stabilization
*   **Goal:** 100% reliable Read/Write to CY7C67200 internal registers.
*   **Action:** Validate the canonical HPI map (`DATA=0`, `MAILBOX=1`, `ADDR=2`, `STATUS=3`) with no dummy reads.
*   **Verification:** `scripts/cy_hpi_ladder_probe.py` reports `CY_HPI_RUNG1_PASS timing=<profile> map=canonical`.
*   **2026-05-10 status:** checksum `0x033E503E` preserves Ethernet and shows live HPI data visibility (`0x5555` readback), but `test_c000_alias.py` still proves address aliasing across `0x1000..0xC000`. Rung 1 is improved but not complete.
*   **2026-05-11 research update:** the old swapped-map and dummy-read diagnostics are no longer accepted as Rung 1 evidence because HPI data-port accesses auto-increment the CY address pointer. Use the canonical no-dummy ladder probe before retrying LCP.
*   **2026-05-11 rebuild update:** rebuilt pulse-only checksum `0x033B0DAC` failed the Ethernet gate and was archived. The board is restored to checksum `0x033C9E9A`.

### Rung 2: LCP Handshake (The "Handshake" Rung)
*   **Goal:** Successfully execute the Local Communications Processor (LCP) reset.
*   **Action:** Send `0xFA50` (COMM_RESET) to the Mailbox and wait for `0x0FED` (COMM_ACK) in the Mailbox Status.
*   **Verification:** `scripts/lcp_handshake.py` reports `LCP Handshake SUCCESS!`.

### Rung 3: SIE & BIOS Initialization
*   **Goal:** Enable the Serial Interface Engines (SIE) for USB Host mode.
*   **Action:** Load the full DE2 BIOS image to CY RAM and issue `SIE1_INIT` via LCP.
*   **Verification:** `HPI_STATUS` bit 4 (`SIE1MSG`) asserts; reading `SIE1MSG_REG` returns initialization success.

### Rung 4: USB Enumeration (HID Discovery)
*   **Goal:** Detect a connected USB device (Mouse/Keyboard).
*   **Action:** Run the HID polling loop in the VexRiscv firmware.
*   **Verification:** UART logs show `CONNECTED` and valid USB descriptors being read from the device.

### Rung 5: Peripheral Expansion (SD Card)
*   **Goal:** Integrate the SD Card core for persistent storage.
*   **Action:** Rebuild SoC with `with_sdcard=True` and verify pin `A23` (part of the breakthrough search) is not conflicted.
*   **Verification:** `firmware/src/main.c` (SD variant) reads Sector 0 and dumps the MBR to UART.

## 3. Execution Strategy

### Phase A: Gateware Freeze
1.  Run `scripts/build_soc.sh` to stage the fixed RTL.
2.  Perform a clean host build of the bitstream.
3.  Validate Ethernet on this new build immediately. **If Ethernet fails, the ladder stops.**

### Phase B: Firmware Migration
1.  Update `firmware/src/cy7c67200_hpi.c` to use the "Fast Timing" pulse logic.
2.  Keep CY HPI register offsets canonical: data `0x000`, mailbox `0x004`, address `0x008`, status `0x00c`. The older "Index 15" swapped mapping is only a negative-control diagnostic.

### Phase C: The Full Climb
1.  Program the board with the "Frozen" gateware.
2.  Deploy the updated firmware.
3.  Observe UART for the sequential climb through Rungs 2, 3, and 4.

## 4. Conflict Management
- **Pin A23:** Identified as `rgmii_eth1_rx_data[2]`. Do not use for other purposes.
- **Interrupts:** Keep `D5` as `int0`. Use `E5` only as a secondary diagnostic.
