# Evidence Bundle Schema

Each hardware run should create:

```text
artifacts/usb-hpi-runs/YYYYMMDD-HHMMSS/
```

## Required files

```text
manifest.json
notes.md
uart-com3.log
ethernet-port1-check.txt
board-gpio-smoke-test.txt
```

## Optional but recommended files

```text
wishbone-csr-dump.txt
hpi-source-probe.txt
litescope-hpi.csv
signaltap-hpi.csv
agentkvm2usb-status.json
vga-frame-before.jpg
vga-frame-after.jpg
```

## Beagle 12 files

```text
beagle12/
  capture.tdc
  summary.txt
  exported.csv
  notes.md
```

## AgentWebCam files

```text
webcam/
  board-before.jpg
  board-after.jpg
  leds.jpg
  sevenseg.jpg
  lcd.jpg
  switches.jpg
  board-run.mp4
```

## manifest.json template

```json
{
  "run_id": "YYYYMMDD-HHMMSS",
  "git_commit": "",
  "branch": "",
  "sof_file": "",
  "sof_sha256": "",
  "firmware_mode": "",
  "com_port": "COM3",
  "ethernet_port": "DE2-115 Port 1",
  "agentwebcam_camera": 1,
  "beagle12_used": false,
  "beagle12_capture_files": [],
  "usb_test_topology": "",
  "switch_positions": "",
  "baseline_ethernet_pass": false,
  "baseline_gpio_pass": false,
  "hpi_readback_result": "",
  "usb_packet_result": "",
  "conclusion": ""
}
```

## notes.md template

```text
# Run Notes

## Goal

## Hardware topology

## Switch positions

## Commands run

## COM3 observations

## Ethernet observations

## HPI observations

## Beagle 12 observations

- Reset observed:
- SOF observed:
- SETUP observed:
- Enumeration observed:
- BAD_SYNC:
- Other errors:

## AgentWebCam observations

## Conclusion

## Next action
```
