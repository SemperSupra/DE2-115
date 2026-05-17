#!/usr/bin/env python3
import os
import json
import time
import subprocess
import argparse
from datetime import datetime

MANIFEST_TEMPLATE = {
    "run_id": "",
    "git_commit": "",
    "branch": "",
    "sof_file": "",
    "sof_sha256": "",
    "firmware_mode": "",
    "com_port": "COM3",
    "ethernet_port": "DE2-115 Port 1",
    "agentwebcam_camera": 1,
    "beagle12_used": False,
    "beagle12_capture_files": [],
    "usb_test_topology": "",
    "switch_positions": "",
    "baseline_ethernet_pass": False,
    "baseline_gpio_pass": False,
    "hpi_readback_result": "",
    "usb_packet_result": "",
    "conclusion": ""
}

NOTES_TEMPLATE = """# Run Notes

## Goal
{goal}

## Hardware topology
{topology}

## Switch positions

## Commands run
- `python scripts\\ethernet_low_speed_test.py --ping-count 50 --csr-loops 512 --bind-port 1235`
- `python scripts\\board_gpio_smoke_test.py --start-server --port 1239`

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
"""

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True).strip()
    except subprocess.CalledProcessError:
        return ""

def main():
    parser = argparse.ArgumentParser(description="Prepare an evidence bundle for DE2-115 HPI/USB debug runs.")
    parser.add_argument("--goal", default="Task 1: Capture Beagle 12 PC Reference and Terasic Host Demo", help="Goal of this hardware run")
    parser.add_argument("--topology", default="PC host -> Beagle 12 -> simple USB mouse", help="Hardware USB topology")
    parser.add_argument("--beagle", action="store_true", help="Set beagle12_used to true in manifest")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join("artifacts", "usb-hpi-runs", timestamp)

    # Create directories
    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(os.path.join(run_dir, "beagle12"), exist_ok=True)
    os.makedirs(os.path.join(run_dir, "webcam"), exist_ok=True)

    # Get Git info
    git_commit = run_cmd("git rev-parse HEAD")
    branch = run_cmd("git rev-parse --abbrev-ref HEAD")

    # Prepare manifest
    manifest = MANIFEST_TEMPLATE.copy()
    manifest["run_id"] = timestamp
    manifest["git_commit"] = git_commit
    manifest["branch"] = branch
    manifest["beagle12_used"] = args.beagle
    manifest["usb_test_topology"] = args.topology

    with open(os.path.join(run_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    # Prepare notes.md
    with open(os.path.join(run_dir, "notes.md"), "w") as f:
        f.write(NOTES_TEMPLATE.format(goal=args.goal, topology=args.topology))

    # Touch empty log/txt files
    open(os.path.join(run_dir, "uart-com3.log"), "w").close()
    open(os.path.join(run_dir, "ethernet-port1-check.txt"), "w").close()
    open(os.path.join(run_dir, "board-gpio-smoke-test.txt"), "w").close()

    print(f"Created evidence bundle structure at: {run_dir}")
    print("Please populate the files as you run your hardware tests.")

if __name__ == "__main__":
    main()
