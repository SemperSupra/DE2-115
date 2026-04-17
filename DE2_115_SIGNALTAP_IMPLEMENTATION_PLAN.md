# DE2-115 SignalTap Implementation Plan

This document expands on the overarching debugging strategy by detailing concrete SignalTap configurations for each confirmed peripheral on the DE2-115 LiteX SoC.

## 1. USB HPI Bridge (CY7C67200)

**Context**: The CY7C67200 requires precise timing for correct Host Port Interface (HPI) access. Currently, the bridge configuration registers are accessible but the device fails to initialize, requiring deep timing and signalling sweep.

*   **Target Clock Domain**: `sys` (50 MHz default system clock, as it drives the Wishbone bus).
*   **Signals to Tap**:
    *   **External Pads**: `usb_otg_data[15:0]`, `usb_otg_addr[1:0]`, `usb_otg_cs_n`, `usb_otg_rd_n`, `usb_otg_wr_n`, `usb_otg_rst_n`, `usb_otg_dack_n[1:0]`, `usb_otg_dreq[1:0]`, `usb_otg_int0`, `usb_otg_int1`
    *   **Internal State**: `cy7c67200_wb_bridge` state machine registers (e.g. `state`, `count`), `i_wb_cyc`, `i_wb_stb`, `o_wb_ack`
*   **Trigger Conditions**:
    *   **Hardware Event**: Falling edge of `usb_otg_cs_n` (indicates the start of an HPI transaction).
    *   **Software Cross-Trigger**: Trigger on the Wishbone read/write assertion (`i_wb_stb & i_wb_cyc`) targeting the HPI configuration address.
*   **Sample Depth & Configuration**: 2048 or 4096 samples. The state machine wait cycles might stretch transactions, so a deeper buffer is needed to capture full read/write sequences. Pre-trigger position: 10% to capture bus state prior to transaction start.
*   **File**: `usb_hpi_debug.stp`

## 2. Ethernet RGMII (Marvell 88E1111)

**Context**: The physical link is established (LED indications), but the PHY register 1 reports "Link Down" back to the MAC. MDIO access is fully operational.

*   **Target Clock Domain**: `eth` (125 MHz clock driving the Ethernet core).
*   **Signals to Tap**:
    *   **External Pads**: `rgmii_eth_rx_ctl`, `rgmii_eth_rx_data[3:0]`, `rgmii_eth_tx_ctl`, `rgmii_eth_tx_data[3:0]`, `rgmii_eth_rst_n`
    *   **MDIO (Optional but useful)**: `rgmii_eth_mdio`, `rgmii_eth_mdc` (if correlated with link state changes, though usually slow enough for `sys` domain).
*   **Trigger Conditions**:
    *   **Hardware Event**: Rising edge of `rgmii_eth_rx_ctl` (indicates valid incoming frame data or valid in-band status from the PHY).
    *   **Link Status Event**: Changes in the `rgmii_eth_rx_data` bus when `rx_ctl` is low (some PHYs signal status this way) or explicit value matching for 1000Mbps link indications.
*   **Sample Depth & Configuration**: 4096 samples. Pre-trigger position: 50%. Since RGMII runs at 125MHz DDR, ensuring high sample depth gives more context around link-status broadcasts.
*   **File**: `eth_rgmii_debug.stp`

## 3. VGA Output

**Context**: The custom 640x480 test pattern generator is functioning but is isolated from the main CPU framebuffer.

*   **Target Clock Domain**: `vga` (25 MHz pixel clock).
*   **Signals to Tap**:
    *   **External Pads**: `vga_r[7:0]`, `vga_g[7:0]`, `vga_b[7:0]`, `vga_blank_n`, `vga_sync_n`, `ping_hsync`, `ping_vsync`
    *   **Internal State**: `h_cnt[10:0]`, `v_cnt[10:0]` from the `SimpleVGA` module.
*   **Trigger Conditions**:
    *   **Hardware Event**: Falling edge of `ping_vsync` (captures the start of a new frame, useful for macroscopic timing).
    *   **Hardware Event**: specific coordinate match, e.g. `h_cnt == 640 && v_cnt == 480` to debug blanking porch transitions.
*   **Sample Depth & Configuration**: 8192 samples (to capture a decent segment of a scanline). Pre-trigger position: 20%.
*   **File**: `vga_debug.stp`

## 4. LCD Controller

**Context**: The HD44780-compatible LCD interface is exposed via GPIO but not fully characterized.

*   **Target Clock Domain**: `sys` (50 MHz).
*   **Signals to Tap**:
    *   **External Pads**: `lcd_data[7:0]`, `lcd_en`, `lcd_rw`, `lcd_rs`, `lcd_on`, `lcd_blon`
*   **Trigger Conditions**:
    *   **Hardware Event**: Rising edge of `lcd_en` (captures the precise moment data is latched into the LCD controller).
*   **Sample Depth & Configuration**: 1024 samples. The LCD interface is extremely slow compared to the 50MHz clock. State capture method might be needed if GPIO bit-banging generates long delays.
*   **File**: `lcd_debug.stp`

## 5. 7-Segment Displays

**Context**: Driven by GPIO, straightforward but useful for basic diagnostics.

*   **Target Clock Domain**: `sys` (50 MHz).
*   **Signals to Tap**:
    *   **External Pads**: Outputs for `hex0` through `hex7` (all 7 segments `a` to `g` for each display).
*   **Trigger Conditions**:
    *   **Hardware Event**: Any change on a specific `hex` group bus (e.g. `hex0` changes value).
*   **Sample Depth & Configuration**: 512 samples. Very low frequency updates.
*   **File**: `seven_seg_debug.stp`

## 6. LEDs (Green and Red)

**Context**: Simple GPIO outputs used for board status indication.

*   **Target Clock Domain**: `sys` (50 MHz).
*   **Signals to Tap**:
    *   **External Pads**: `leds_g[8:0]`, `leds_r[17:0]`
*   **Trigger Conditions**:
    *   **Hardware Event**: Any edge (rising or falling) on specific status LEDs (e.g., triggering on the LED used for Ethernet link indication to capture surrounding events).
*   **Sample Depth & Configuration**: 512 samples.
*   **File**: `leds_debug.stp`

## 7. SDRAM (IS42S16320)

**Context**: The primary memory for the VexRiscv CPU and potentially future framebuffers.

*   **Target Clock Domain**: `sys_ps` (Phase-shifted 50 MHz clock for SDRAM timing alignment).
*   **Signals to Tap**:
    *   **External Pads** (If needed for low-level debug): `sdram_dq`, `sdram_a`, `sdram_ba`, `sdram_cas_n`, `sdram_ras_n`, `sdram_we_n`, `sdram_cs_n`.
    *   **Internal State**: LiteDRAM controller `dfi` interface signals (more useful than raw pads for logical debugging).
*   **Trigger Conditions**:
    *   **Hardware Event**: Falling edge of `sdram_cs_n` and `sdram_ras_n` (Active command).
    *   **Data Errors**: Trigger on specific `dfi` read data mismatches if a memory test is running.
*   **Sample Depth & Configuration**: 4096 samples. Memory access bursts are fast, deep sampling is required to capture entire transaction blocks.
*   **File**: `sdram_debug.stp`
