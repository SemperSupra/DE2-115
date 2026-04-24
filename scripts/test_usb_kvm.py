import sys
import os
import time
import serial
import threading

# Add KVM SDK to path
sys.path.append(os.path.join(os.getcwd(), 'tools', 'AgentKVM2USB'))
from epiphan_sdk import EpiphanKVM_SDK

def monitor_thread(ser, stop_event, results):
    print("[Monitor] Started UART listener...")
    while not stop_event.is_set():
        if ser.in_waiting:
            line = ser.readline().decode('ascii', errors='ignore').strip()
            if line:
                print(f"[Board] {line}")
                if "KBD:" in line or "MSE:" in line:
                    results.append(line)
        time.sleep(0.01)

def run_test():
    port = "COM3"
    baud = 115200
    
    print(f"Connecting to {port}...")
    try:
        ser = serial.Serial(port, baud, timeout=1)
    except Exception as e:
        print(f"Error: {e}")
        return

    stop_event = threading.Event()
    results = []
    t = threading.Thread(target=monitor_thread, args=(ser, stop_event, results))
    t.start()

    print("Initializing KVM SDK...")
    sdk = EpiphanKVM_SDK()
    
    print("\n--- Phase 1: Keyboard Test ---")
    test_keys = "JULES"
    for char in test_keys:
        print(f"Sending key: {char}")
        sdk.type(char)
        time.sleep(0.5)

    print("\n--- Phase 2: Mouse/Touch Test ---")
    # Small square movement using click (absolute)
    movements = [(0.1, 0.1), (0.2, 0.1), (0.2, 0.2), (0.1, 0.2)]
    for x, y in movements:
        print(f"Clicking at: x={x}, y={y}")
        sdk.click(x, y)
        time.sleep(0.5)

    print("\nTest sequence complete. Waiting for final board logs...")
    time.sleep(2)
    
    stop_event.set()
    t.join()
    ser.close()
    sdk.close()

    print("\n--- Test Summary ---")
    kbd_events = [r for r in results if "KBD:" in r]
    mse_events = [r for r in results if "MSE:" in r]
    
    print(f"Keyboard events detected: {len(kbd_events)}")
    print(f"Mouse/Touch events detected: {len(mse_events)}")
    
    if len(kbd_events) > 0 or len(mse_events) > 0:
        print("\nUSB KVM TEST SUCCESSFUL (at least partially)!")
    else:
        print("\nUSB KVM TEST FAILED: No events detected on board.")

if __name__ == "__main__":
    run_test()
