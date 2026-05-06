import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import matplotlib.pyplot as plt
import cv2
import numpy as np

from image_process.camera import capture_from_camera
from sketch_module import generate_sketch
from skeleton_module import skeletonize
from line_extraction import extract_lines_from_skeleton


def main():

    # ===================== CAPTURE =====================
    img_path = capture_from_camera()

    if img_path is None:
        print("❌ Capture failed")
        return

    print("✅ Image captured:", img_path)

    # ===================== SKETCH =====================
    sketch = generate_sketch(img_path)

    if sketch is None:
        print("❌ Sketch generation failed")
        return

    print("\n--- DEBUG INFO ---")
    print("Shape:", sketch.shape)
    print("Unique values:", set(sketch.flatten()))

    # ===================== SHOW IMAGE =====================
    original = cv2.imread(img_path)
    if original is None:
        raise ValueError(f"❌ Failed to load image from: {img_path}")

    original = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)

    plt.figure(figsize=(10, 5))

    plt.subplot(1, 2, 1)
    plt.imshow(original)
    plt.title("Captured Image")
    plt.axis('off')

    plt.subplot(1, 2, 2)
    plt.imshow(sketch, cmap='gray')
    plt.title("Sketch")
    plt.axis('off')

    plt.show()

    # ===================== SKELETON =====================
    skeleton = skeletonize(sketch)

    plt.figure(figsize=(10, 5))

    plt.subplot(1, 2, 1)
    plt.imshow(sketch, cmap='gray')
    plt.title("Sketch")

    plt.subplot(1, 2, 2)
    plt.imshow(skeleton, cmap='gray')
    plt.title("Skeleton")

    plt.show()

    # ===================== LINE EXTRACTION =====================
    lines = extract_lines_from_skeleton(skeleton)
    print("Extracted lines:", len(lines))

    # ===================== BUILD TRAJECTORY =====================
    x_actual = []
    y_actual = []

    for line in lines:
        for pt in line:
            x_actual.append(pt[0])
            y_actual.append(pt[1])

    # ===================== FINAL TRAJECTORY VIS =====================
    plt.figure()
    plt.plot(x_actual, y_actual, 'r')
    plt.gca().invert_yaxis()
    plt.axis('equal')
    plt.title("Final Trajectory (No Pen Lift)")
    plt.show()


if __name__ == "__main__":
    main()