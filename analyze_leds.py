import cv2
import numpy as np

def main():
    img = cv2.imread('enet_leds_only.jpg')
    if img is None: return
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for i, cnt in enumerate(contours):
        if cv2.contourArea(cnt) < 2: continue
        x, y, w, h = cv2.boundingRect(cnt)
        print(f"Spot {i}: x={x}, y={y}, w={w}, h={h}")
        crop = img[max(0,y-10):y+h+10, max(0,x-10):x+w+10]
        cv2.imwrite(f'spot_{i}.jpg', crop)

if __name__ == "__main__":
    main()
