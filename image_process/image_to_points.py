import cv2
import numpy as np
import mediapipe as mp


# ================== CAMERA ==================
def capture_from_camera(save_path="captured.png"):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Camera not working")

    print("Press SPACE to capture")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        cv2.imshow("Camera", frame)
        key = cv2.waitKey(1)

        if key == 32:
            cv2.imwrite(save_path, frame)
            break

    cap.release()
    cv2.destroyAllWindows()
    return save_path

