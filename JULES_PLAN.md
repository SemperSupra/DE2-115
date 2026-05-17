# JULES_PLAN.md - DE2-115 SoC Evolution Strategy

## 1. Vision

Transform the DE2-115 LiteX SoC from a manual bring-up prototype into a verified Ethernet and USB host platform with repeatable hardware-in-the-loop checks.

## 2. Current Board Baseline

- Firmware executes and UART diagnostics are reliable.
- VGA is working.
- Ethernet Port 1 is active by default.
- PHY17 responds over MDIO and the current forced 10/100 image reports `INBAND=0000000B`.
- Host ping to `192.168.178.50` passes.
- Etherbone CSR access passes through `litex_server` on a non-conflicting host TCP port; port `1235` was used for the successful identifier and LED CSR test.
- USB HPI write cycles are proven at the FPGA bus/pin-sample level.
- USB HPI read cycles still return `0x0000` from the CY7C67200, blocking LCP ACK and host initialization. An Etherbone reset/sample-offset sweep also returned only zeroes.

## 3. Priority Phase 1: Infrastructure & Reliability

### A. Path Sanitization

Problem: Docker-generated Quartus files can contain absolute Linux paths that are invalid for host-side Quartus on Windows.

Action: Add a pre-synthesis or post-generation check that fails if generated Quartus inputs contain invalid container-only paths.

Goal: prevent silent black-box CPU/peripheral failures.

### B. Automated HIL Testing

Action: Create a `verify_boot.py` script that:

1. Programs the FPGA.
2. Captures UART output.
3. Checks for expected status lines such as `CONFIGURING MDIO DELAYS`, `INBAND=`, and HPI debug lines.
4. Optionally captures VGA through `AgentKVM2USB`.

Goal: make bring-up regressions visible without manual log reading.

## 4. Priority Phase 2: USB Host Controller (CY7C67200)

### A. HPI Readback Root Cause

Context: The bridge now writes `0x1234` onto the HPI bus successfully, but CY reads remain zero:

```text
HPI DBG WR ... sample=00001234 cy=00001234
HPI DBG RD ... sample=00000000 cy=00000000
HPI0 read_data: rst=0 hpi_rst_n=1 cs_n=0 rd_n=0 wr_n=1 addr=0 data=0000
```

Action:

- Review and refine the local on-FPGA HPI pad snapshot implementation when
  delegated. Current Jules review session: `14997796971249417694`.
- Confirm whether debug register offsets `0x100` through `0x124` map correctly
  through LiteX/Etherbone to the bridge local debug words.
- Confirm whether the snapshot count points are correct for address/data writes
  and canonical reads.
- Compare against a known-good Terasic USB demo bitstream on the same board if possible.

Goal: restore basic HPI memory/control-register readback.

### Current Delegation Boundaries

- Jules should handle isolated RTL/script review and small patches.
- Jules should not own hardware programming, Ethernet regression, or board
  swaps.
- GitHub Actions now has manual dispatch enabled and passed Static Checks
  `25988084275` plus LiteX SoC Build `25988084379`.
- Local execution owns Quartus compile, FPGA programming, Etherbone hardware
  tests, and board swaps across the four available DE2-115 boards.

### B. LCP Firmware Flow

Blocked until HPI readback is fixed.

Once unblocked:

- Verify memory write/read at `0x1000`.
- Verify LCP blob readback.
- Verify `COMM_JUMP2CODE` produces `COMM_ACK`.
- Verify `SIE1_INIT` and `USB_RESET` ACKs.

## 5. Priority Phase 3: Ethernet Baseline

Context: Ethernet is no longer blocked at physical/in-band link. Forced 10/100 mode passes ping and Etherbone CSR access.

Action:

- Preserve the forced 10/100 image as the regression baseline.
- Add a scripted ping plus Etherbone CSR smoke test to the HIL flow.
- Revisit gigabit RGMII separately with `ETH0`/`ETX0` source-probe captures.

Goal: keep `192.168.178.50` reachable from the host and prevent regressions while USB is debugged.

## 6. Success Metrics

- `run.bat` or the equivalent build flow completes from firmware through SOF.
- UART log shows `INBAND=0000000B` or another known-good Ethernet status.
- Host can reach `192.168.178.50` over the intended LiteEth/Etherbone path.
- USB memory readback returns written data.
- LCP load produces `COMM_ACK`.
- USB host flow reaches device-connect message `0x1000`.
