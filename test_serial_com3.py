import serial
import time
import sys

def test_serial():
    port = "COM3"
    baud = 115200
    timeout = 5

    print(f"Opening {port} at {baud} baud...")
    try:
        ser = serial.Serial(port, baud, timeout=timeout)
    except Exception as e:
        print(f"Error opening port: {e}")
        sys.exit(1)

    # Give it a moment to reset/stabilize if needed
    time.sleep(1)
    ser.reset_input_buffer()

    print("Waiting for startup message...")
    start_time = time.time()
    found_hello = False
    while time.time() - start_time < 10:
        line = ser.readline().decode('ascii', errors='ignore').strip()
        if line:
            print(f"RX: {line}")
        if "Hello from DE2-115!" in line:
            found_hello = True
            break

    if not found_hello:
        print("Warning: Did not see 'Hello from DE2-115!' message, but continuing with echo test...")

    test_str = "JULES"
    print(f"Sending test string: {test_str}")
    for char in test_str:
        ser.write(char.encode('ascii'))
        time.sleep(0.1)
        
        # Check for echo
        echo_found = False
        echo_start = time.time()
        while time.time() - echo_start < 2:
            line = ser.readline().decode('ascii', errors='ignore').strip()
            if line:
                print(f"RX: {line}")
            if f"Echo: {char}" in line:
                echo_found = True
                break
        
        if not echo_found:
            print(f"Error: Did not receive echo for {char}")
            ser.close()
            sys.exit(1)

    print("\n--- Serial Test SUCCESSFUL ---")
    ser.close()

if __name__ == "__main__":
    test_serial()
