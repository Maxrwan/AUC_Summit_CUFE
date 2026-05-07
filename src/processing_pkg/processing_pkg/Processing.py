import sys
import os
import cv2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import numpy as np

from sketch_module import generate_sketch
from skeleton_module import skeletonize
from line_extraction import extract_strokes


# ===================== CONSTANTS =====================

Z_LIFT = 0.1
Z_DRAW = 0.0
DT = 0.02
MAX_LINES = 400
MAX_SEGMENT = 10   # 🔥 CRITICAL: gap detection threshold


# ===================== FILTER =====================

def filter_lines(lines, min_length=5):
    return [line for line in lines if len(line) >= min_length]


# ===================== MERGE =====================

def merge_lines(lines, dist_thresh=6):

    merged = []
    used = [False] * len(lines)

    for i in range(len(lines)):
        if used[i]:
            continue

        current = lines[i]
        used[i] = True

        changed = True

        while changed:
            changed = False

            for j in range(len(lines)):
                if used[j]:
                    continue

                l2 = lines[j]

                p1_start = np.array(current[0])
                p1_end = np.array(current[-1])

                p2_start = np.array(l2[0])
                p2_end = np.array(l2[-1])

                if np.linalg.norm(p1_end - p2_start) < dist_thresh:
                    current = current + l2
                elif np.linalg.norm(p1_end - p2_end) < dist_thresh:
                    current = current + l2[::-1]
                elif np.linalg.norm(p1_start - p2_end) < dist_thresh:
                    current = l2 + current
                elif np.linalg.norm(p1_start - p2_start) < dist_thresh:
                    current = l2[::-1] + current
                else:
                    continue

                used[j] = True
                changed = True

        merged.append(current)

    return merged


# ===================== SMOOTH =====================

def smooth_line(line):
    if len(line) < 3:
        return line

    new = []
    for i in range(1, len(line)-1):
        x = (line[i-1][0] + line[i][0] + line[i+1][0]) / 3
        y = (line[i-1][1] + line[i][1] + line[i+1][1]) / 3
        new.append((x, y))

    return new


# ===================== ORDER =====================

def order_lines(lines):

    if not lines:
        return []

    remaining = lines.copy()
    ordered = []

    current = remaining.pop(0)
    ordered.append(current)

    while remaining:

        best_idx = 0
        best_dist = float('inf')
        best_line = None

        current_end = np.array(current[-1]) # type: ignore

        for i, line in enumerate(remaining):

            start = np.array(line[0])
            end = np.array(line[-1])

            d_start = np.linalg.norm(current_end - start)
            d_end = np.linalg.norm(current_end - end)

            if d_start < best_dist:
                best_dist = d_start
                best_idx = i
                best_line = line

            if d_end < best_dist:
                best_dist = d_end
                best_idx = i
                best_line = line[::-1]

        current = best_line
        ordered.append(current)
        remaining.pop(best_idx)

    return ordered


# ===================== MOTION =====================

def move_to_point(x, y, z, tx, ty, tz):

    dx = tx - x
    dy = ty - y
    dz = tz - z

    vx = dx / DT
    vy = dy / DT
    vz = dz / DT

    return [(tx, ty, tz, vx, vy, vz)], tx, ty, tz


# ===================== CORE =====================

def reconnect_close_lines(lines, dist_thresh=12):

    new_lines = []
    used = [False] * len(lines)

    for i in range(len(lines)):
        if used[i]:
            continue

        current = lines[i]
        used[i] = True

        extended = True

        while extended:
            extended = False

            for j in range(len(lines)):
                if used[j]:
                    continue

                l2 = lines[j]

                d1 = np.linalg.norm(np.array(current[-1]) - np.array(l2[0]))
                d2 = np.linalg.norm(np.array(current[-1]) - np.array(l2[-1]))

                if d1 < dist_thresh:
                    current = current + l2
                elif d2 < dist_thresh:
                    current = current + l2[::-1]
                else:
                    continue

                used[j] = True
                extended = True

        new_lines.append(current)

    return new_lines

def process_lines(lines):

    if len(lines) == 0:
        raise ValueError("No lines provided")

    print("Original strokes:", len(lines))

    # 🔥 merge first
    lines = merge_lines(lines, dist_thresh=6)
    print("After merging:", len(lines))

    # 🔥 filter
    lines = filter_lines(lines, min_length=3)
    print("After filtering:", len(lines))

    # 🔥 remove crazy long junk
    def remove_outliers(lines, max_len=150):
        clean = []
        for line in lines:
            length = np.linalg.norm(np.array(line[0]) - np.array(line[-1]))
            if length < max_len:
                clean.append(line)
        return clean

    lines = remove_outliers(lines)

    lines = reconnect_close_lines(lines, dist_thresh = 10)
    print("After reconnecting:", len(lines))
    
    # 🔥 order
    lines = order_lines(lines)

    # limit
    lines = lines[:MAX_LINES]
    print("Using lines:", len(lines))

    # 🔥 smooth
    lines = [smooth_line(line) for line in lines]

    # ===================== TRAJECTORY =====================

    x_actual, y_actual, z_actual = [], [], []
    vx_all, vy_all, vz_all = [], [], []

    x, y = lines[0][0]
    z = Z_LIFT

    for line in lines:

        # move above start
        traj, x, y, z = move_to_point(x, y, z, line[0][0], line[0][1], Z_LIFT)
        for t in traj:
            x_actual.append(t[0]); y_actual.append(t[1]); z_actual.append(t[2])
            vx_all.append(t[3]); vy_all.append(t[4]); vz_all.append(t[5])

        # pen down
        traj, x, y, z = move_to_point(x, y, z, x, y, Z_DRAW)
        for t in traj:
            x_actual.append(t[0]); y_actual.append(t[1]); z_actual.append(t[2])
            vx_all.append(t[3]); vy_all.append(t[4]); vz_all.append(t[5])

        # 🔥 DRAW WITH GAP DETECTION
        prev_pt = None

        for pt in line:

            if prev_pt is not None:
                dist = np.linalg.norm(np.array(pt) - np.array(prev_pt))

                if dist > MAX_SEGMENT:
                    # lift
                    traj, x, y, z = move_to_point(x, y, z, x, y, Z_LIFT)
                    for t in traj:
                        x_actual.append(t[0]); y_actual.append(t[1]); z_actual.append(t[2])
                        vx_all.append(t[3]); vy_all.append(t[4]); vz_all.append(t[5])

                    # move
                    traj, x, y, z = move_to_point(x, y, z, pt[0], pt[1], Z_LIFT)
                    for t in traj:
                        x_actual.append(t[0]); y_actual.append(t[1]); z_actual.append(t[2])
                        vx_all.append(t[3]); vy_all.append(t[4]); vz_all.append(t[5])

                    # down
                    traj, x, y, z = move_to_point(x, y, z, x, y, Z_DRAW)
                    for t in traj:
                        x_actual.append(t[0]); y_actual.append(t[1]); z_actual.append(t[2])
                        vx_all.append(t[3]); vy_all.append(t[4]); vz_all.append(t[5])

            # normal draw
            traj, x, y, z = move_to_point(x, y, z, pt[0], pt[1], Z_DRAW)
            for t in traj:
                x_actual.append(t[0]); y_actual.append(t[1]); z_actual.append(t[2])
                vx_all.append(t[3]); vy_all.append(t[4]); vz_all.append(t[5])

            prev_pt = pt

        # lift at end
        traj, x, y, z = move_to_point(x, y, z, x, y, Z_LIFT)
        for t in traj:
            x_actual.append(t[0]); y_actual.append(t[1]); z_actual.append(t[2])
            vx_all.append(t[3]); vy_all.append(t[4]); vz_all.append(t[5])

    return x_actual, y_actual, z_actual, vx_all, vy_all, vz_all


# ===================== PIPELINE =====================

def process_image(img_path):

    sketch = generate_sketch(img_path)
    sketch = cv2.resize(sketch, None, fx=0.3, fy=0.3)

    skeleton = skeletonize(sketch)
    lines = extract_strokes(skeleton)

    if lines is None or len(lines) == 0:
        raise ValueError("No strokes extracted")

    print("Extracted strokes:", len(lines))

    return process_lines(lines)