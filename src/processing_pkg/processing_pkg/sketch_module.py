import cv2
import numpy as np

def generate_sketch(img):

    if img is None:
        raise ValueError("Invalid image input")

    img = cv2.resize(img, (320, 320))

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 🔥 better smoothing (preserves edges)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)

    # 🔥 adaptive thresholds (CRUCIAL)
    v = np.median(gray)

    lower = int(np.clip(0.66 * v, 40, 80)) # 80
    upper = int(np.clip(1.33 * v, 100, 160)) # 160 

    edges = cv2.Canny(gray, lower, upper)
    edges = cv2.threshold(edges, 50, 255, cv2.THRESH_BINARY)[1]

    # 🔥 clean noise but KEEP structure
    kernel = np.ones((3,3), np.uint8)    
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    
    return edges