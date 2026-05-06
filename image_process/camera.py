import cv2
import numpy as np


# ================== CAMERA ==================
def capture_from_camera(save_path="captured.png", crop=False):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Camera not working")

    print("Press SPACE to capture | ESC to exit")

    captured = False
    frame = None

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        cv2.imshow("Camera", frame)
        key = cv2.waitKey(1)

        # SPACE → capture
        if key == 32:
            captured = True
            break

        # ESC → cancel
        if key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

    if not captured or frame is None:
        print("⚠️ Capture cancelled")
        return None

    # ================== SAVE ORIGINAL ==================
    cv2.imwrite(save_path, frame)

    # ================== OPTIONAL CROP ==================
    if crop:
        h, w = frame.shape[:2]
        cropped = frame[h//4:3*h//4, w//4:3*w//4]

        cropped_path = save_path.replace(".png", "_cropped.png")
        cv2.imwrite(cropped_path, cropped)

        return cropped_path

    return save_path