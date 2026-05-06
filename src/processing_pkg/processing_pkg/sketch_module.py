import cv2
import numpy as np


def generate_sketch(img_path):

    img = cv2.imread(img_path)

    if img is None:
        raise ValueError(f"Failed to read image: {img_path}")

    # resize for consistency
    img = cv2.resize(img, (320, 320))

    # grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # edge detection
    edges = cv2.Canny(blurred, 50, 150)

    # invert → black lines on white background
    sketch = 255 - edges

    # ensure binary
    _, sketch = cv2.threshold(sketch, 127, 255, cv2.THRESH_BINARY)

    return sketch