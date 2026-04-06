import sys
import os
import time

# Add the SDK directory to path
sys.path.append(os.path.join(os.getcwd(), "tools", "AgentKVM2USB"))

from epiphan_sdk import EpiphanKVM_SDK

def main():
    print("Initializing Epiphan KVM2USB SDK...")
    try:
        sdk = EpiphanKVM_SDK()
        
        print("Running Autotune...")
        sdk.autotune()
        time.sleep(2)
        
        print("Checking device status...")
        status = sdk.get_status()
        print(f"Status: {status}")
        
        print("Capturing VGA output...")
        output_file = "vga_capture.jpg"
        sdk.get_screen(output_file)
        
        if os.path.exists(output_file):
            print(f"Success! VGA output captured to {output_file}")
        else:
            print("Error: Capture failed, file not created.")
            
        sdk.close()
    except Exception as e:
        print(f"Failed to interact with Epiphan KVM2USB: {e}")

if __name__ == "__main__":
    main()
