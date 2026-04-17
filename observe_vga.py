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
        
        time.sleep(2) # Give it time to initialize capture
        
        print("Checking device status...")
        status = sdk.get_status()
        print(f"Status: {status}")
        
        print("Capturing VGA output...")
        # get_screen returns the absolute path of the captured file
        path = sdk.get_screen("vga_diag")
        
        if path and os.path.exists(path):
            print(f"Success! VGA output captured to: {path}")
            # Copy it to a fixed name for easy access if needed
            import shutil
            shutil.copy(path, "vga_capture.jpg")
            print("Copied to vga_capture.jpg")
        else:
            print("Error: Capture failed, file not created.")
            
        sdk.close()
    except Exception as e:
        print(f"Failed to interact with Epiphan KVM2USB: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
