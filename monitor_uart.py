import serial
import time
import sys

def monitor_uart():
    port = "COM3"
    baud = 115200
    timeout = 1

    print(f"Monitoring {port} at {baud} baud... (Ctrl+C to stop)")
    try:
        ser = serial.Serial(port, baud, timeout=timeout)
    except Exception as e:
        print(f"Error opening port: {e}")
        sys.exit(1)

    try:
        while True:
            line = ser.readline().decode('ascii', errors='ignore').strip()
            if line:
                print(f"[{time.strftime('%H:%M:%S')}] {line}")
            else:
                # Still alive?
                pass
    except KeyboardInterrupt:
        print("\nStopping monitor.")
    finally:
        ser.close()

if __name__ == "__main__":
    monitor_uart()
