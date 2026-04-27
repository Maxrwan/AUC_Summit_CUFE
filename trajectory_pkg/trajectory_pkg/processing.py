"""
Title: Processing Unit (AUC Summit)
Description: Generation of trajectory and velocity profiles using point lists for contours
Inputs: Point lists 
Outputs: Trajectory and velocity profiles
Authors: - Fatmaelzahraa Ashraf 
         - Marwan Ahmed
Date: 26/5/2026
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import splprep, splev


# ===================== helper functions =====================

def lift_z(z, target_z, dt):
    vz_list = []
    z_path = []
    
    while z < target_z:
        vz = Z_SPEED
        z += vz *dt
        
        if z > target_z:
            z = target_z
        
        vz_list.append(vz)
        z_path.append(z)
        
    return z, vz_list, z_path 

def lower_z(z, target_z, dt):
    vz_list = []
    z_path = []

    while z > target_z:
        vz = -Z_SPEED
        z += vz * dt

        if z < target_z:
            z = target_z

        vz_list.append(vz)
        z_path.append(z)

    return z, vz_list, z_path


# Example: multiple strokes (like drawing a square + triangle)
lines = [
    [(0,0), (1,0), (1,1), (0,1), (0,0)],     # closed square
    [(2,0), (3,1), (4,0)],                   # open V shape
    [(5,0), (5,1), (6,1), (6,0), (5,0)],     # another closed shape
    [(7,0), (8,1), (9,1), (10,0)]            # open polyline
]

# Defining the Z axis 
Z_UP = 0.1
Z_SPEED = 0.01


# =================== Spline Generation ===================

# split lines into x and y points
x_points = []
y_points = []
splines = []
line = lines[0]

# for line in lines:
#     x_points = [p[0] for p in line]
#     y_points = [p[1] for p in line]

def generate_spline(line):
    x_points = [p[0] for p in line]
    y_points = [p[1] for p in line]

    # adapt k
    m = len(line)
    k = min(3, m - 1)
    
    tck , u = splprep([x_points, y_points], s = 0, k = k)
    #splines.append(tck)

    u_dense = np.linspace(0, 1, 1000)

    x_s, y_s = splev(u_dense, tck)
    dx, dy = splev(u_dense, tck, der = 1)

    dx = np.array(dx)
    dy = np.array(dy)
    x_s = np.array(x_s)
    y_s = np.array(y_s)
    
    du = u_dense[1] - u_dense[0]
    ds = np.hypot(dx, dy) * du
    
    s = np.cumsum(ds)
    L = s[-1]
    
    return {
        "x": x_s,
        "y": y_s,
        "dx": dx,
        "dy": dy,
        "s": s,
        "L": L,
        "start": np.array([x_s[0], y_s[0]]),
        "end": np.array([x_s[-1], y_s[-1]])
    }

# =================== Direction Calculation ===================

def choose_direction(current_pos, spline):
    d_start = np.linalg.norm(current_pos - spline["start"])
    d_end = np.linalg.norm(current_pos - spline["end"])
    
    if d_start < d_end:
        return spline, spline["end"]
    else:
        spline_rev = {
            "x": spline["x"][::-1],
            "y": spline["y"][::-1],
            "dx": -spline["dx"][::-1],
            "dy": -spline["dy"][::-1],
            "s": spline["s"],  # OK for now
            "L": spline["L"],
            "start": spline["end"],
            "end": spline["start"]
        }
        return spline_rev, spline_rev["end"]
    
    
# =================== Transition generation ===================

def generate_transition(p1, p2):
    
    x = np.linspace(p1[0], p2[0], 200)
    y = np.linspace(p1[1], p2[1], 200)
    
    dx = np.gradient(x)
    dy = np.gradient(y)
    
    ds = np.hypot(dx, dy)
    s = np.cumsum(ds)
    L = s[-1]
    
    return {
        "x": x,
        "y": y,
        "dx": dx,
        "dy": dy,
        "s": s,
        "L": L,
        "start": np.array(p1),
        "end": np.array(p2)
    }
    
# =================== Simple Ordering ===================

splines = [generate_spline(line) for line in lines]

ordered_splines = []
current_pos = splines[0]["start"]

remaining = splines.copy()

while remaining:
    best_idx = None 
    best_spline = None 
    best_endpos = None
    best_dist = np.inf
    
    for i, spline in enumerate(remaining):
        d_start = np.linalg.norm(current_pos - spline["start"])
        d_end = np.linalg.norm(current_pos - spline["end"])
        
        if d_start < d_end:
            dist = d_start
            chosen_spline = spline
            end_pos = spline["end"]
        else:
            chosen_spline = {
                "x": spline["x"][::-1],
                "y": spline["y"][::-1],
                "dx": -spline["dx"][::-1],
                "dy": -spline["dy"][::-1],
                "s": spline["s"],
                "L": spline["L"],
                "start": spline["end"],
                "end": spline["start"]
            }
            dist = d_end
            end_pos = chosen_spline["end"]
            
        if dist < best_dist:
            best_idx = i
            best_spline = chosen_spline
            best_endpos = end_pos
            best_dist = dist
    
    ordered_splines.append(best_spline)
    current_pos = best_endpos
    assert best_idx is not None
    remaining.pop(best_idx)

# =================== Velocity Profile ===================

# General trapezoidal profile fucntion 
# acceleration phase, time: 0 to Ta
# constant velocity phase, time: Ta to Ta + Tb
# deceleration phase, time: Ta + Tb to Tf

class TrapezoidalProfile: 
    def __init__(self, L, vmax, a):
        self.L = L
        self.vmax = vmax
        self.a = a
        
        #Acceleration time 
        self.Ta = vmax / a
        
        #Distance covered during acceleration 
        self.Sa = 0.5 * a * self.Ta**2
        
        #Check if full trapezoidal is possible 
        if 2 * self.Sa < L:
            self.Tc = (L - 2 * self.Sa) / vmax
            self.vpeak = vmax
        else:
            #Triangle profile 
            self.Ta = np.sqrt(L / a)
            self.Tc = 0
            self.vpeak = a * self.Ta
            self.Sa = 0.5 * a * self.Ta**2
        
        #Total time 
        self.Tf = 2 * self.Ta + self.Tc
        
    def get_state(self, t):
        # Returns velocity v(t) and position s(t) at specified time t 
        if t < 0:
            return 0, 0
        elif t < self.Ta:
            v = self.a * t
            s = 0.5 * self.a * t**2
        elif t < self.Ta + self.Tc:
            v = self.vpeak 
            s = self.Sa + self.vpeak * (t - self.Ta)
        elif t < self.Tf:
            t_dec = t - self.Ta - self.Tc 
            v = self.vpeak - self.a * t_dec 
            s = self.L - 0.5 * self.a * (self.Tf - t)**2
        else: 
            v = 0
            s = self.L
        return v, s
    
# =================== Trajectory Profile ===================

dt = 0.01 # 100 Hz

vx_all = []
vy_all = []
vz_all = []
x_actual = []
y_actual = []
z_actual = []

x = ordered_splines[0]["x"][0]
y = ordered_splines[0]["y"][0]
z = 0

x_actual.append(x)
y_actual.append(y)

for i, spline in enumerate(ordered_splines):

    # ADD TRANSITION (if not first spline)
    if i > 0:
        prev_end = ordered_splines[i-1]["end"]
        curr_start = spline["start"]

        # Z - axis transition
        y, vz_list, z_path = lift_z(z, Z_UP, dt)
        
        for vz, z_val in zip(vz_list, z_path):
            vx_all.append(0)
            vy_all.append(0)
            vz_all.append(vz)
            
            x_actual.append(x)
            y_actual.append(y)
            z_actual.append(z_val)

        transition = generate_transition(prev_end, curr_start)

        profile = TrapezoidalProfile(L=transition["L"], vmax=1.0, a=0.5)

        for t in np.arange(0, profile.Tf, dt):
            v, s_current = profile.get_state(t)

            idx = np.searchsorted(transition["s"], s_current)
            idx = min(idx, len(transition["dx"]) - 1)
            
            dx_s = transition["dx"][idx]
            dy_s = transition["dy"][idx]
            
            norm = np.hypot(dx_s, dy_s) + 1e-8

            vx = v * dx_s / norm
            vy = v * dy_s / norm
            vz = 0

            vx_all.append(vx)
            vy_all.append(vy)
            vz_all.append(vz)
            
            x += vx * dt
            y += vy * dt

            x_actual.append(x)
            y_actual.append(y)
            z_actual.append(z)

        # Z - axis transition
        y, vz_list, z_path = lower_z(z, 0, dt)
        
        for vz, z_val in zip(vz_list, z_path):
            vx_all.append(0)
            vy_all.append(0)
            vz_all.append(vz)
            
            x_actual.append(x)
            y_actual.append(y)
            z_actual.append(z_val)


    # NOW DRAW THE ACTUAL SPLINE
    profile = TrapezoidalProfile(L=spline["L"], vmax=1.0, a=0.5)

    for t in np.arange(0, profile.Tf, dt):
        v, s_current = profile.get_state(t)

        idx = np.searchsorted(spline["s"], s_current)
        idx = min(idx, len(spline["dx"]) - 1)

        dx_s = spline["dx"][idx]
        dy_s = spline["dy"][idx]

        norm = np.hypot(dx_s, dy_s) + 1e-8

        vx = v * dx_s / norm
        vy = v * dy_s / norm
        vz = 0

        vx_all.append(vx)
        vy_all.append(vy)
        vz_all.append(vz)

        x += vx * dt
        y += vy * dt

        x_actual.append(x)
        y_actual.append(y)
        z_actual.append(z)
        
# =================== Velocity + Distance Analysis ===================

vx_all = np.array(vx_all)
vy_all = np.array(vy_all)

# total speed magnitude
v_total = np.hypot(vx_all, vy_all)

# time vector
t_values = np.arange(0, len(v_total) * dt, dt)

# cumulative distance (integrating speed)
s_total = np.cumsum(v_total * dt)

# =================== Old Code ===================
# vx_list = []
# vy_list = []

# for t in np.arange(0, profile.Tf, dt):
#     v, s_current = profile.get_state(t)
    
#     idx = np.searchsorted(s, s_current)
#     idx = min(idx, len(dx) - 1)
    
#     dx_s = dx[idx]
#     dy_s = dy[idx]
    
#     norm = np.hypot(dx_s, dy_s) + 1e-8
    
#     vx = v * dx_s / norm 
#     vy = v * dy_s / norm 
    
#     vx_list.append(vx)
#     vy_list.append(vy)
    
# x_actual = [x_s[0]]
# y_actual = [y_s[0]]

# x = x_s[0]
# y = y_s[0]

# for vx, vy in zip(vx_list, vy_list):
#     x += vx *dt
#     y += vy *dt
#     x_actual.append(x)
#     y_actual.append(y)

# =================== Plotting ===================

plt.figure()

for spline in ordered_splines:
    plt.plot(spline["x"], spline["y"], '--')
    
# actual paths
plt.plot(x_actual, y_actual, 'r', label = 'Actual Path')

for i in range(len(ordered_splines)-1):
    p1 = ordered_splines[i]["end"]
    p2 = ordered_splines[i+1]["start"]
    plt.plot([p1[0], p2[0]], [p1[1], p2[1]], 'k--')
    
plt.axis('equal')
plt.legend()
plt.title("Multi-Spline Drawing")
plt.show()


# Velocity Values Print 
print(vx_all, vy_all)

for i, (vx, vy) in enumerate(zip(vx_all, vy_all)):
    print(f"Step {i}: Vx={vx:.4f}, Vy={vy:.4f}")
    
# Velocity and Distance Plots 
fig, axs = plt.subplots(2, 1)

# Velocity plot
axs[0].plot(t_values, v_total)
axs[0].set_title('Full Velocity Profile (All Splines)')
axs[0].set_xlabel('Time (s)')
axs[0].set_ylabel('Speed (m/s)')

# Distance plot
axs[1].plot(t_values, s_total)
axs[1].set_title('Total Distance Along Drawing')
axs[1].set_xlabel('Time (s)')
axs[1].set_ylabel('Distance (m)')

fig.subplots_adjust(hspace=0.4)
plt.show()

z_actual = np.array(z_actual)
t_values = np.arange(0, len(z_actual) * dt, dt)

plt.figure()
plt.plot(t_values, z_actual)
plt.title("Z Motion (Pen Up / Down)")
plt.xlabel("Time (s)")
plt.ylabel("Z Height")
plt.show()
     
# =================== Plotting (Old)===================
# fig, axs = plt.subplots(2, 1)
# axs[0].plot(t_values, v_list)
# axs[0].set_title('Velocity Profile')
# axs[0].set_xlabel('Time (s)')

# axs[1].plot(t_values, s_list)
# axs[1].set_title('Distance Profile')
# axs[1].set_xlabel('Distance (m)')

# fig.subplots_adjust(hspace=0.5)

# plt.figure()
# plt.plot(x_s, y_s, '--', label = 'Desired Path')
# plt.plot(x_actual, y_actual, label = 'Simulated')
# plt.legend()
# plt.axis('equal')
# plt.title('Path Tracking Result')
# plt.xlabel('X (m)')
# plt.ylabel('Y (m)')

# plt.show()

# =================== Export ===================
def generate_trajectory(points):
    return vx_all, vy_all, vz_all, dt


