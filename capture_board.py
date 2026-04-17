import cv2
import os

def main():
    print("Capturing from webcam (index 0) in high res...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("Error: Could not open webcam index 0.")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    # Try to get some frames to settle
    for i in range(20):
        ret, frame = cap.read()
    
    if ret:
        filename = "board_photo_hd.jpg"
        cv2.imwrite(filename, frame)
        print(f"Success! Board photo captured to: {filename}")
        print(f"Resolution: {frame.shape[1]}x{frame.shape[0]}")
    else:
        print("Error: Could not read frame from webcam.")
    
    cap.release()

if __name__ == "__main__":
    main()
