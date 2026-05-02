#!/usr/bin/env python3
import rospy
import threading
from std_msgs.msg import Float32MultiArray

class AxisPID:
    def __init__(self, kp, ki, kd, dt=0.05):
        self.kp = kp; self.ki = ki; self.kd = kd; self.dt = dt
        self.integral = 0.0; self.prev_error = 0.0; self.target = 0.0
    def set_target(self, t):
        self.target = t
    def update(self, current):
        error = self.target - current
        self.integral += error * self.dt
        deriv = (error - self.prev_error) / self.dt if self.dt > 0 else 0
        self.prev_error = error
        return self.kp*error + self.ki*self.integral + self.kd*deriv

class GantryPIDController:
    def __init__(self):
        rospy.init_node('gantry_pid_controller')

        # Subscribers
        self.path_sub = rospy.Subscriber('/marwan_topic', Float32MultiArray, self.path_callback)
        self.fb_xy_sub = rospy.Subscriber('/encoder_feedback_xy', Float32MultiArray, self.xy_feedback_cb)
        self.fb_z_sub  = rospy.Subscriber('/encoder_feedback_z', Float32MultiArray, self.z_feedback_cb)

        # Publishers
        self.cmd_xy_pub = rospy.Publisher('/motor_commands_xy', Float32MultiArray, queue_size=1)
        self.cmd_z_pub  = rospy.Publisher('/motor_commands_z', Float32MultiArray, queue_size=1)

        # PID controllers
        self.pid_x = AxisPID(4.99, 0.4, 0.8556)
        self.pid_y = AxisPID(4.99, 0.4, 0.8556)
        self.pid_z = AxisPID(4.99, 0.4, 0.8556)

        # Mechanism
        self.drum_circ = 0.19478  # m
        self.ppr = 2002.7

        # Current RPM feedback
        self.rpm_x = 0.0; self.rpm_y = 0.0; self.rpm_z = 0.0

        # Path queue and control rate
        self.path_buffer = []
        self.path_index = 0
        self.rate = rospy.Rate(20)  # 20 Hz
        self.lock = threading.Lock()
        
        self.loop_count = 0

        rospy.loginfo("=" * 60)
        rospy.loginfo("GANTRY PID CONTROLLER STARTED (DEBUG MODE)")
        rospy.loginfo(f"  PID gains: Kp=4.99  Ki=0.4  Kd=0.8556")
        rospy.loginfo(f"  Drum circumference: {self.drum_circ} m")
        rospy.loginfo(f"  Control rate: 20 Hz")
        rospy.loginfo("=" * 60)

    def path_callback(self, msg):
        num_waypoints = len(msg.data) // 3
        new_path = []
        for i in range(num_waypoints):
            vx = msg.data[3*i]
            vy = msg.data[3*i+1]
            vz = msg.data[3*i+2]
            new_path.append((vx, vy, vz))
        with self.lock:
            self.path_buffer = new_path
            self.path_index = 0
        rospy.loginfo(f"✅ Received path: {len(new_path)} waypoints")
        for i, (vx, vy, vz) in enumerate(new_path[:5]):  # Show first 5
            rospy.loginfo(f"  [{i}] vx={vx:.3f} vy={vy:.3f} vz={vz:.3f}")

    def xy_feedback_cb(self, msg):
        if len(msg.data) >= 2:
            self.rpm_x = msg.data[0]
            self.rpm_y = msg.data[1]

    def z_feedback_cb(self, msg):
        if len(msg.data) >= 1:
            self.rpm_z = msg.data[0]

    def vel_to_rpm(self, vel_mps):
        return (vel_mps / self.drum_circ) * 60.0

    def rpm_to_vel(self, rpm):
        return (rpm / 60.0) * self.drum_circ

    def run(self):
        while not rospy.is_shutdown():
            self.loop_count += 1

            with self.lock:
                if self.path_buffer and self.path_index < len(self.path_buffer):
                    vx, vy, vz = self.path_buffer[self.path_index]
                    self.path_index += 1
                else:
                    vx = vy = vz = 0.0

            # Convert to RPM
            target_x = self.vel_to_rpm(vx)
            target_y = self.vel_to_rpm(vy)
            target_z = self.vel_to_rpm(vz)

            # PID
            self.pid_x.set_target(target_x)
            self.pid_y.set_target(target_y)
            self.pid_z.set_target(target_z)
            cmd_x = self.pid_x.update(self.rpm_x)
            cmd_y = self.pid_y.update(self.rpm_y)
            cmd_z = self.pid_z.update(self.rpm_z)

            # IMPORTANT DEBUG: Print what we're sending
            if self.loop_count % 20 == 0:  # Every 20th loop (1 second)
                rospy.loginfo("=" * 50)
                rospy.loginfo(f"LOOP {self.loop_count}")
                rospy.loginfo(f"  Target vel (m/s):  vx={vx:.3f}  vy={vy:.3f}  vz={vz:.3f}")
                rospy.loginfo(f"  Target RPM:        tx={target_x:.2f}  ty={target_y:.2f}  tz={target_z:.2f}")
                rospy.loginfo(f"  Feedback RPM:      fx={self.rpm_x:.2f}  fy={self.rpm_y:.2f}  fz={self.rpm_z:.2f}")
                rospy.loginfo(f"  PID OUTPUT RPM:    cx={cmd_x:.2f}  cy={cmd_y:.2f}  cz={cmd_z:.2f}")
                rospy.loginfo("=" * 50)

            # Send to ESPs
            xy_msg = Float32MultiArray()
            xy_msg.data = [cmd_x, cmd_y]
            self.cmd_xy_pub.publish(xy_msg)

            z_msg = Float32MultiArray()
            z_msg.data = [cmd_z]
            self.cmd_z_pub.publish(z_msg)

            self.rate.sleep()

if __name__ == '__main__':
    try:
        controller = GantryPIDController()
        controller.run()
    except rospy.ROSInterruptException:
        pass