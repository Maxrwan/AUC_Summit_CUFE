import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import numpy as np
import matplotlib.pyplot as plt

from image_process.camera import capture_from_camera


# ===================== INPUT =====================

img_path = capture_from_camera()

if img_path is None:
    raise ValueError("Image capture failed")


# 🔥 TEMP placeholder
def get_lines_from_image(img_path):
    return [
        [(0, 0), (1, 1), (2, 2)],
        [(4, 4), (5, 5)]
    ]


lines = get_lines_from_image(img_path)

if len(lines) == 0:
    raise ValueError("No lines extracted")

print("DEBUG: lines:", len(lines))


# ===================== ORDER LINES =====================

def order_lines(lines):
    ordered = []
    current = np.array(lines[0][0])
    remaining = lines.copy()

    while remaining:
        best_idx = None
        best_dist = np.inf

        for i, line in enumerate(remaining):
            start = np.array(line[0])
            d = np.linalg.norm(current - start)

            if d < best_dist:
                best_dist = d
                best_idx = i

        best = remaining.pop(best_idx)
        ordered.append(best)
        current = np.array(best[-1])

    return ordered


lines = order_lines(lines)


# ===================== TRAJECTORY SETTINGS =====================

dt = 0.02
speed_draw = 0.5

z_draw = 0.0  # always drawing plane

x_actual, y_actual, z_actual = [], [], []
vx_all, vy_all, vz_all = [], [], []


# ===================== MOTION FUNCTION =====================

def move_to_point(x, y, z, tx, ty, tz, speed):

    dx = tx - x
    dy = ty - y
    dz = tz - z

    dist = np.sqrt(dx**2 + dy**2 + dz**2)

    if dist < 1e-6:
        return [], x, y, z

    steps = max(int(dist / (speed * dt)), 1)

    traj = []

    for i in range(steps):
        alpha = (i + 1) / steps

        nx = x + alpha * dx
        ny = y + alpha * dy
        nz = z + alpha * dz

        vx = (nx - x) / dt
        vy = (ny - y) / dt
        vz = (nz - z) / dt

        traj.append((nx, ny, nz, vx, vy, vz))

        x, y, z = nx, ny, nz

    return traj, x, y, z


# ===================== BUILD TRAJECTORY =====================

# 🔥 Start directly at first point on drawing plane
x, y = lines[0][0]
z = z_draw

for line in lines:

    for pt in line:
        traj, x, y, z = move_to_point(x, y, z, pt[0], pt[1], z_draw, speed_draw)

        for t in traj:
            x_actual.append(t[0])
            y_actual.append(t[1])
            z_actual.append(t[2])
            vx_all.append(t[3])
            vy_all.append(t[4])
            vz_all.append(t[5])


# ===================== SAVE =====================

output_file = "/Users/marwansaber/University/Design/Summit/AUC_Summit_CUFE/trajectory_profiles/image_traj.txt"

os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, "w") as f:
    for i in range(len(x_actual)):
        f.write(
            f"{x_actual[i]:.6f} {y_actual[i]:.6f} {z_actual[i]:.6f} "
            f"{vx_all[i]:.6f} {vy_all[i]:.6f} {vz_all[i]:.6f}\n"
        )

print("✅ Saved:", output_file)


# ===================== VIS =====================

plt.figure()
plt.plot(x_actual, y_actual, 'r')
plt.axis('equal')
plt.title("Trajectory WITHOUT Pen Lift")
plt.show()