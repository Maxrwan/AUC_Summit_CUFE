import sys
import os
import cv2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import numpy as np

import matplotlib.pyplot as plt

from image_process.camera import capture_from_camera
from skeleton_module import skeletonize
from sketch_module import generate_sketch
from line_extraction import extract_strokes
from Processing import process_lines


OUTPUT_PATH = "/Users/marwansaber/trajectory_output.txt"


def main():

    # ===================== CAPTURE =====================
    img_path = capture_from_camera()

    if img_path is None:
        print("❌ Capture failed")
        return

    print("✅ Image captured:", img_path)

    img = cv2.imread(img_path)

    if img is None:
        print("❌ Failed to load image")
        return

    # ===================== CROP =====================
    h, w = img.shape[:2]
    img = img[h//4:3*h//4, w//4:3*w//4]
    
    # ===================== FACE-FOCUSED MASK =====================
    h, w = img.shape[:2]

    # create center mask (ellipse)
    mask = np.zeros((h, w), dtype=np.uint8)

    center = (w // 2, h // 2)
    axes = (int(w * 0.35), int(h * 0.45))  # tune if needed

    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)

    # apply mask
    img_masked = cv2.bitwise_and(img, img, mask=mask)

    # ===================== EDGE =====================
    gray = cv2.cvtColor(img_masked, cv2.COLOR_BGR2GRAY)    
    gray = cv2.GaussianBlur(gray, (5,5), 0)
    sketch = generate_sketch(img_masked)
    # ===================== VIS =====================
    plt.figure(figsize=(10,5))
    plt.subplot(1,2,1)
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.title("Cropped Image")
    plt.axis('off')

    plt.subplot(1,2,2)
    plt.imshow(sketch, cmap='gray')
    plt.title("Canny")
    plt.axis('off')
    plt.show()

    # ===================== SKELETON =====================
    skeleton = skeletonize(sketch)

    plt.figure()
    plt.imshow(skeleton, cmap='gray')
    plt.title("Skeleton")
    plt.axis('off')
    plt.show()

    # ===================== STROKES =====================
    lines = extract_strokes(skeleton)

    if lines is None or len(lines) == 0:
        print("❌ No strokes found")
        return
    
    if len(lines) < 5:
        print("Too few strokes found")
        return

    print("Extracted strokes:", len(lines))

    # ===================== PROCESS =====================
    x, y, z, vx, vy, vz = process_lines(lines)

    print("Trajectory points:", len(x))

    # ===================== SAVE =====================
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        for i in range(len(x)):
            f.write(
                f"{x[i]:.6f} {y[i]:.6f} {z[i]:.6f} "
                f"{vx[i]:.6f} {vy[i]:.6f} {vz[i]:.6f}\n"
            )

    print(f"✅ Trajectory saved to: {OUTPUT_PATH}")

    # ===================== VIS =====================
    plt.figure(figsize=(6,6))

    x_draw, y_draw = [], []
    x_move, y_move = [], []

    for i in range(len(x)):
        if abs(z[i] - 0.0) < 1e-6:  # drawing
            x_draw.append(x[i])
            y_draw.append(y[i])
        else:            # pen lifted
            x_move.append(x[i])
            y_move.append(y[i])

    # 🔴 drawing
    plt.plot(x_draw, y_draw, 'r', linewidth=0.8)
    plt.plot(x_move, y_move, 'b--', linewidth=0.7, alpha=0.6)

    plt.gca().invert_yaxis()
    plt.gca().set_aspect('equal')

    plt.title("Trajectory (Red = Draw, Blue = Move)")
    plt.show()


if __name__ == "__main__":
    main()