import sys
sys.path.append('tools/AgentKVM2USB')
sys.path.append('tools/AgentWebCam')

from epiphan_sdk import EpiphanKVM_SDK
import cv2
import time

def main():
    print("Initializing Epiphan KVM2USB SDK...")
    sdk = EpiphanKVM_SDK()
    
    print("Typing on keyboard: 'X'...")
    sdk.type("X")
    time.sleep(1)
    
    print("Capturing Webcam (DE2-115 Board LCD)...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if cap.isOpened():
        # Read a few frames to let camera auto-exposure adjust
        for _ in range(5):
            cap.read()
            time.sleep(0.1)
            
        ret, frame = cap.read()
        if ret:
            cv2.imwrite("lcd_interaction_test_X.jpg", frame)
            print("Saved to lcd_interaction_test_X.jpg")
        cap.release()
    
    sdk.close()

if __name__ == "__main__":
    main()
