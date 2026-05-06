import cv2
import numpy as np


def skeletonize(binary_img):
    """
    Convert binary image to 1-pixel skeleton
    """

    # ensure binary (0 or 255)
    _, img = cv2.threshold(binary_img, 127, 255, cv2.THRESH_BINARY)

    img = img // 255  # convert to 0/1

    skeleton = np.zeros_like(img, dtype=np.uint8)

    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))

    while True:
        eroded = cv2.erode(img, kernel)
        opened = cv2.dilate(eroded, kernel)

        temp = cv2.subtract(img, opened)
        skeleton = cv2.bitwise_or(skeleton, temp)

        img = eroded.copy()

        if cv2.countNonZero(img) == 0:
            break

    skeleton = skeleton * 255  # back to 0/255

    return skeleton