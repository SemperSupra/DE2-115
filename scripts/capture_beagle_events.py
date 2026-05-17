#!/usr/bin/env python3
import sys
import os
import subprocess
import glob
from datetime import datetime

BEAGLE_API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Downloads", "beagle-api-windows-x86_64-v6.00", "python"))

def find_latest_run_dir():
    base_dir = os.path.join("artifacts", "usb-hpi-runs")
    if not os.path.isdir(base_dir):
        return None
    runs = glob.glob(os.path.join(base_dir, "*"))
    if not runs:
        return None
    return max(runs, key=os.path.getctime)

def main():
    if not os.path.isdir(BEAGLE_API_DIR):
        print(f"Error: Beagle API directory not found at {BEAGLE_API_DIR}")
        sys.exit(1)

    print("Checking for Beagle devices...")
    detect_script = os.path.join(BEAGLE_API_DIR, "detect.py")
    try:
        detect_out = subprocess.check_output([sys.executable, detect_script], text=True)
        print(detect_out)
        if "No devices found" in detect_out:
            print("Error: Please plug in the Beagle 12 USB analyzer before capturing.")
            sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error running detect.py: {e}")
        sys.exit(1)

    run_dir = find_latest_run_dir()
    if not run_dir:
        print("Error: No evidence bundle directory found. Please run prepare_evidence_bundle.py first.")
        sys.exit(1)

    beagle_dir = os.path.join(run_dir, "beagle12")
    os.makedirs(beagle_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = os.path.join(beagle_dir, f"capture_{timestamp}.txt")
    
    events_to_capture = 1000
    if len(sys.argv) > 1:
        try:
            events_to_capture = int(sys.argv[1])
        except ValueError:
            pass

    capture_script = os.path.join(BEAGLE_API_DIR, "capture_usb12.py")
    
    print(f"Starting capture of {events_to_capture} events...")
    print("Please UNPLUG and RE-PLUG the target USB device NOW to generate connect/reset/enumeration traffic.")
    print(f"Output will be saved to: {out_file}")
    
    try:
        with open(out_file, "w") as f:
            proc = subprocess.Popen([sys.executable, capture_script, str(events_to_capture)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                sys.stdout.write(line)
                f.write(line)
                f.flush()
            proc.wait()
            
        print("\nCapture finished successfully.")
    except KeyboardInterrupt:
        print("\nCapture interrupted by user.")
    except Exception as e:
        print(f"\nError during capture: {e}")

if __name__ == "__main__":
    main()