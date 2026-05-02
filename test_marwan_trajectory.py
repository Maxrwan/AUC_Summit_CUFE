#!/usr/bin/env python3
"""
Test script to send trajectory data to /marwan_topic
Usage:
  rosrun atom_pnp test_marwan_trajectory.py              # Interactive mode
  rosrun atom_pnp test_marwan_trajectory.py auto         # Automated sequence
  rosrun atom_pnp test_marwan_trajectory.py x 50         # X-axis at 50 mm/s
  rosrun atom_pnp test_marwan_trajectory.py xy 50        # XY diagonal at 50 mm/s
  rosrun atom_pnp test_marwan_trajectory.py z 30         # Z-axis at 30 mm/s
  rosrun atom_pnp test_marwan_trajectory.py rect 80      # Rectangle at 80 mm/s
  rosrun atom_pnp test_marwan_trajectory.py sine 50      # Sine wave at 50 mm/s
  rosrun atom_pnp test_marwan_trajectory.py stop         # Stop all motors
"""

import rospy
from std_msgs.msg import Float32MultiArray
import math
import sys

class MarwanTestPublisher:
    def __init__(self):
        rospy.init_node('marwan_test_publisher', anonymous=True)
        
        # Publisher for trajectory
        self.marwan_pub = rospy.Publisher('/marwan_topic', Float32MultiArray, queue_size=10)
        
        # Subscribers to monitor feedback
        self.fb_xy_sub = rospy.Subscriber('/encoder_feedback_xy', Float32MultiArray, self.xy_feedback_cb)
        self.fb_z_sub = rospy.Subscriber('/encoder_feedback_z', Float32MultiArray, self.z_feedback_cb)
        self.cmd_xy_sub = rospy.Subscriber('/motor_commands_xy', Float32MultiArray, self.xy_cmd_cb)
        self.cmd_z_sub = rospy.Subscriber('/motor_commands_z', Float32MultiArray, self.z_cmd_cb)
        
        rospy.loginfo("=" * 60)
        rospy.loginfo("Marwan Test Publisher Ready")
        rospy.loginfo("=" * 60)
        
    def xy_feedback_cb(self, msg):
        if len(msg.data) >= 4:
            rospy.loginfo_throttle(2, 
                "[FEEDBACK XY] RPM: (%.2f, %.2f) | Pos: (%.2f, %.2f) mm" % 
                (msg.data[0], msg.data[1], msg.data[2], msg.data[3]))
    
    def z_feedback_cb(self, msg):
        if len(msg.data) >= 2:
            rospy.loginfo_throttle(2, 
                "[FEEDBACK Z] RPM: %.2f | Pos: %.2f mm" % 
                (msg.data[0], msg.data[1]))
    
    def xy_cmd_cb(self, msg):
        if len(msg.data) >= 2:
            rospy.loginfo_throttle(2, 
                "[CMD XY] %.2f, %.2f RPM" % (msg.data[0], msg.data[1]))
    
    def z_cmd_cb(self, msg):
        if len(msg.data) >= 1:
            rospy.loginfo_throttle(2, 
                "[CMD Z] %.2f RPM" % msg.data[0])
    
    def send_trajectory(self, waypoints):
        """Send trajectory to /marwan_topic"""
        data = []
        for (vx, vy, vz) in waypoints:
            data.extend([vx, vy, vz])
        
        msg = Float32MultiArray()
        msg.data = data
        
        rospy.loginfo("=" * 60)
        rospy.loginfo("Sending trajectory: %d waypoints" % len(waypoints))
        for i, (vx, vy, vz) in enumerate(waypoints):
            rospy.loginfo("  [%d] vx=%.3f vy=%.3f vz=%.3f m/s" % (i, vx, vy, vz))
        rospy.loginfo("=" * 60)
        
        self.marwan_pub.publish(msg)
    
    def test_x_axis(self, speed_mms=50):
        """Test X axis at specified speed in mm/s"""
        speed = speed_mms / 1000.0  # Convert mm/s to m/s
        rospy.loginfo("\n" + "=" * 60)
        rospy.loginfo("TEST: X-Axis at %.0f mm/s" % speed_mms)
        rospy.loginfo("=" * 60)
        
        waypoints = [
            (speed, 0.0, 0.0),
            (speed, 0.0, 0.0),
            (speed, 0.0, 0.0),
            (speed/2, 0.0, 0.0),  # Slow down
            (0.0, 0.0, 0.0),      # Stop
        ]
        self.send_trajectory(waypoints)
    
    def test_y_axis(self, speed_mms=50):
        """Test Y axis at specified speed in mm/s"""
        speed = speed_mms / 1000.0
        rospy.loginfo("\n" + "=" * 60)
        rospy.loginfo("TEST: Y-Axis at %.0f mm/s" % speed_mms)
        rospy.loginfo("=" * 60)
        
        waypoints = [
            (0.0, speed, 0.0),
            (0.0, speed, 0.0),
            (0.0, speed, 0.0),
            (0.0, speed/2, 0.0),
            (0.0, 0.0, 0.0),
        ]
        self.send_trajectory(waypoints)
    
    def test_xy_diagonal(self, speed_mms=50):
        """Test XY diagonal at specified speed in mm/s"""
        speed = speed_mms / 1000.0
        rospy.loginfo("\n" + "=" * 60)
        rospy.loginfo("TEST: XY Diagonal at %.0f mm/s" % speed_mms)
        rospy.loginfo("=" * 60)
        
        waypoints = [
            (speed, speed, 0.0),
            (speed, speed, 0.0),
            (speed*0.7, speed*0.7, 0.0),
            (0.0, 0.0, 0.0),
        ]
        self.send_trajectory(waypoints)
    
    def test_z_axis(self, speed_mms=30):
        """Test Z axis at specified speed in mm/s"""
        speed = speed_mms / 1000.0
        rospy.loginfo("\n" + "=" * 60)
        rospy.loginfo("TEST: Z-Axis at %.0f mm/s" % speed_mms)
        rospy.loginfo("=" * 60)
        
        waypoints = [
            (0.0, 0.0, speed),
            (0.0, 0.0, speed),
            (0.0, 0.0, speed/2),
            (0.0, 0.0, 0.0),
        ]
        self.send_trajectory(waypoints)
    
    def test_rectangle(self, speed_mms=50):
        """Draw rectangle at specified speed in mm/s"""
        speed = speed_mms / 1000.0
        rospy.loginfo("\n" + "=" * 60)
        rospy.loginfo("TEST: Rectangle at %.0f mm/s" % speed_mms)
        rospy.loginfo("=" * 60)
        
        waypoints = [
            # Side 1: +X
            (speed, 0.0, 0.0), (speed, 0.0, 0.0), (0.0, 0.0, 0.0),
            # Side 2: +Y  
            (0.0, speed, 0.0), (0.0, speed, 0.0), (0.0, 0.0, 0.0),
            # Side 3: -X
            (-speed, 0.0, 0.0), (-speed, 0.0, 0.0), (0.0, 0.0, 0.0),
            # Side 4: -Y
            (0.0, -speed, 0.0), (0.0, -speed, 0.0), (0.0, 0.0, 0.0),
        ]
        self.send_trajectory(waypoints)
    
    def test_sine_wave(self, speed_mms=50):
        """Sine wave pattern at specified speed in mm/s"""
        speed = speed_mms / 1000.0
        rospy.loginfo("\n" + "=" * 60)
        rospy.loginfo("TEST: Sine Wave at %.0f mm/s" % speed_mms)
        rospy.loginfo("=" * 60)
        
        waypoints = []
        for i in range(30):
            t = i * 0.1
            vx = speed * 0.7
            vy = speed * 0.5 * math.sin(t * 2)
            vz = 0.0
            waypoints.append((vx, vy, vz))
        
        waypoints.append((0.0, 0.0, 0.0))  # Stop
        self.send_trajectory(waypoints)
    
    def test_circle(self, speed_mms=50):
        """Circle pattern at specified speed in mm/s"""
        speed = speed_mms / 1000.0
        rospy.loginfo("\n" + "=" * 60)
        rospy.loginfo("TEST: Circle at %.0f mm/s" % speed_mms)
        rospy.loginfo("=" * 60)
        
        waypoints = []
        for i in range(40):
            angle = i * (2 * math.pi / 40)
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            vz = 0.0
            waypoints.append((vx, vy, vz))
        
        waypoints.append((0.0, 0.0, 0.0))
        self.send_trajectory(waypoints)
    
    def stop(self):
        """Stop all motors"""
        waypoints = [(0.0, 0.0, 0.0)]
        self.send_trajectory(waypoints)
        rospy.loginfo("Motors stopped")
    
    def interactive_mode(self):
        """Interactive control mode"""
        rospy.loginfo("\n" + "=" * 60)
        rospy.loginfo("INTERACTIVE MODE")
        rospy.loginfo("=" * 60)
        rospy.loginfo("Commands:")
        rospy.loginfo("  x <speed>    - X axis (e.g., x 50)")
        rospy.loginfo("  y <speed>    - Y axis")
        rospy.loginfo("  z <speed>    - Z axis")
        rospy.loginfo("  xy <speed>   - XY diagonal")
        rospy.loginfo("  rect <speed> - Rectangle path")
        rospy.loginfo("  sine <speed> - Sine wave")
        rospy.loginfo("  circle <speed> - Circle")
        rospy.loginfo("  stop         - Stop motors")
        rospy.loginfo("  q            - Quit")
        rospy.loginfo("  OR: vx vy vz  (e.g., 0.05 0.03 0.0)")
        
        while not rospy.is_shutdown():
            try:
                user_input = raw_input("\nEnter command: ").strip().lower()
                
                if user_input == 'q':
                    break
                elif user_input == 'stop':
                    self.stop()
                elif user_input.startswith('x '):
                    speed = float(user_input.split()[1])
                    self.test_x_axis(speed)
                elif user_input.startswith('y '):
                    speed = float(user_input.split()[1])
                    self.test_y_axis(speed)
                elif user_input.startswith('z '):
                    speed = float(user_input.split()[1])
                    self.test_z_axis(speed)
                elif user_input.startswith('xy '):
                    speed = float(user_input.split()[1])
                    self.test_xy_diagonal(speed)
                elif user_input.startswith('rect '):
                    speed = float(user_input.split()[1])
                    self.test_rectangle(speed)
                elif user_input.startswith('sine '):
                    speed = float(user_input.split()[1])
                    self.test_sine_wave(speed)
                elif user_input.startswith('circle '):
                    speed = float(user_input.split()[1])
                    self.test_circle(speed)
                else:
                    parts = user_input.split()
                    if len(parts) == 3:
                        try:
                            vx, vy, vz = float(parts[0]), float(parts[1]), float(parts[2])
                            self.send_trajectory([(vx, vy, vz)])
                        except ValueError:
                            rospy.logerr("Invalid numbers")
                    else:
                        rospy.logwarn("Unknown command")
                        
            except (KeyboardInterrupt, EOFError):
                break
        
        self.stop()


if __name__ == '__main__':
    try:
        tester = MarwanTestPublisher()
        
        if len(sys.argv) == 1:
            # No arguments - interactive mode
            tester.interactive_mode()
        
        elif len(sys.argv) == 2:
            cmd = sys.argv[1].lower()
            if cmd == "auto":
                # Run full auto sequence
                rospy.loginfo("Running automated test sequence...")
                rospy.sleep(2)
                tester.test_x_axis(50)
                rospy.sleep(6)
                tester.test_xy_diagonal(50)
                rospy.sleep(5)
                tester.test_z_axis(30)
                rospy.sleep(5)
                tester.test_rectangle(50)
                rospy.sleep(8)
                tester.stop()
            elif cmd == "stop":
                tester.stop()
            elif cmd == "x":
                tester.test_x_axis(50)
            elif cmd == "y":
                tester.test_y_axis(50)
            elif cmd == "z":
                tester.test_z_axis(30)
            elif cmd == "xy":
                tester.test_xy_diagonal(50)
            elif cmd == "rect":
                tester.test_rectangle(50)
            elif cmd == "sine":
                tester.test_sine_wave(50)
            elif cmd == "circle":
                tester.test_circle(50)
            else:
                # Single number - treat as speed for x-axis
                try:
                    speed = float(cmd)
                    tester.test_x_axis(speed)
                except ValueError:
                    tester.interactive_mode()
        
        elif len(sys.argv) == 3:
            cmd = sys.argv[1].lower()
            speed = float(sys.argv[2])
            
            if cmd == "x":
                tester.test_x_axis(speed)
            elif cmd == "y":
                tester.test_y_axis(speed)
            elif cmd == "z":
                tester.test_z_axis(speed)
            elif cmd == "xy":
                tester.test_xy_diagonal(speed)
            elif cmd == "rect":
                tester.test_rectangle(speed)
            elif cmd == "sine":
                tester.test_sine_wave(speed)
            elif cmd == "circle":
                tester.test_circle(speed)
            else:
                rospy.logerr("Unknown command: %s" % cmd)
        
        else:
            rospy.loginfo("Usage:")
            rospy.loginfo("  rosrun atom_pnp test_marwan_trajectory.py              # Interactive")
            rospy.loginfo("  rosrun atom_pnp test_marwan_trajectory.py auto         # Auto sequence")
            rospy.loginfo("  rosrun atom_pnp test_marwan_trajectory.py x 50         # X-axis 50mm/s")
            rospy.loginfo("  rosrun atom_pnp test_marwan_trajectory.py y 50         # Y-axis 50mm/s")
            rospy.loginfo("  rosrun atom_pnp test_marwan_trajectory.py z 30         # Z-axis 30mm/s")
            rospy.loginfo("  rosrun atom_pnp test_marwan_trajectory.py xy 50        # XY diagonal")
            rospy.loginfo("  rosrun atom_pnp test_marwan_trajectory.py rect 50      # Rectangle")
            rospy.loginfo("  rosrun atom_pnp test_marwan_trajectory.py sine 50      # Sine wave")
            rospy.loginfo("  rosrun atom_pnp test_marwan_trajectory.py circle 50    # Circle")
            rospy.loginfo("  rosrun atom_pnp test_marwan_trajectory.py stop         # Stop")
    
    except rospy.ROSInterruptException:
        pass