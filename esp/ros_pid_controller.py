#!/usr/bin/env python3
# ros_pid_controller.py

import rospy
import numpy as np
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Twist, Pose2D
import math

class ROSPIDController:
    def __init__(self):
        rospy.init_node('ros_pid_controller')
        
        # Publishers and Subscribers
        self.motor_pub = rospy.Publisher('motor_commands', Float32MultiArray, queue_size=10)
        self.cmd_vel_sub = rospy.Subscriber('cmd_vel', Twist, self.cmd_vel_callback)
        self.encoder_sub = rospy.Subscriber('motor_encoders', Float32MultiArray, self.encoder_callback)
        self.pose_sub = rospy.Subscriber('robot_pose', Pose2D, self.pose_callback)
        
        # Robot parameters
        self.wheel_radius = 0.034  # meters
        self.wheel_distance = 0.18  # meters
        
        # Current state
        self.current_left_rpm = 0.0
        self.current_right_rpm = 0.0
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_theta = 0.0
        
        # Target state
        self.target_linear = 0.0
        self.target_angular = 0.0
        
        # PID control variables
        self.linear_integral = 0.0
        self.linear_prev_error = 0.0
        self.angular_integral = 0.0
        self.angular_prev_error = 0.0
        
        # PID gains
        self.Kp_linear = 0.5
        self.Ki_linear = 0.1
        self.Kd_linear = 0.05
        self.Kp_angular = 0.1
        self.Ki_angular = 0.05
        self.Kd_angular = 0.02
        
        # Control loop timing
        self.last_time = rospy.get_time()
        self.control_rate = rospy.Rate(20)  # 20Hz
        
        rospy.loginfo("ROS PID Controller Ready")
        
    def cmd_vel_callback(self, msg):
        """Receive target velocities from cmd_vel"""
        self.target_linear = msg.linear.x
        self.target_angular = msg.angular.z
        rospy.loginfo(f"Target: linear={self.target_linear:.2f}, angular={self.target_angular:.2f}")
    
    def encoder_callback(self, msg):
        """Receive encoder feedback from ESP32"""
        if len(msg.data) >= 4:
            self.current_left_rpm = msg.data[0]
            self.current_right_rpm = msg.data[1]
    
    def pose_callback(self, msg):
        """Receive pose from ESP32"""
        self.current_x = msg.x
        self.current_y = msg.y
        self.current_theta = msg.theta
    
    def rpm_to_linear_angular(self, left_rpm, right_rpm):
        """Convert wheel RPMs to linear and angular velocity"""
        # Convert RPM to wheel speed (m/s)
        left_speed = (left_rpm / 60.0) * (2 * math.pi * self.wheel_radius)
        right_speed = (right_rpm / 60.0) * (2 * math.pi * self.wheel_radius)
        
        # Calculate robot velocities
        linear = (right_speed + left_speed) / 2.0
        angular = (right_speed - left_speed) / self.wheel_distance
        
        return linear, angular
    
    def pid_control(self):
        """Calculate PID output for motor control"""
        current_time = rospy.get_time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        if dt <= 0:
            return 0, 0
        
        # Get current velocities from RPM feedback
        current_linear, current_angular = self.rpm_to_linear_angular(
            self.current_left_rpm, self.current_right_rpm)
        
        # Linear velocity PID
        linear_error = self.target_linear - current_linear
        self.linear_integral += linear_error * dt
        linear_derivative = (linear_error - self.linear_prev_error) / dt
        linear_output = (self.Kp_linear * linear_error + 
                        self.Ki_linear * self.linear_integral + 
                        self.Kd_linear * linear_derivative)
        self.linear_prev_error = linear_error
        
        # Angular velocity PID
        angular_error = self.target_angular - current_angular
        self.angular_integral += angular_error * dt
        angular_derivative = (angular_error - self.angular_prev_error) / dt
        angular_output = (self.Kp_angular * angular_error + 
                         self.Ki_angular * self.angular_integral + 
                         self.Kd_angular * angular_derivative)
        self.angular_prev_error = angular_error
        
        # Convert to individual wheel speeds
        left_speed = linear_output - angular_output * self.wheel_distance / 2
        right_speed = linear_output + angular_output * self.wheel_distance / 2
        
        # Convert back to RPM for ESP32
        left_rpm = (left_speed * 60.0) / (2 * math.pi * self.wheel_radius)
        right_rpm = (right_speed * 60.0) / (2 * math.pi * self.wheel_radius)
        
        return left_rpm, right_rpm
    
    def send_motor_commands(self, left_rpm, right_rpm):
        """Send RPM commands to ESP32"""
        msg = Float32MultiArray()
        msg.data = [left_rpm, right_rpm]
        self.motor_pub.publish(msg)
        
        rospy.loginfo(f"Motor CMD - Left: {left_rpm:.1f} RPM, Right: {right_rpm:.1f} RPM")
    
    def run(self):
        """Main control loop"""
        while not rospy.is_shutdown():
            # Calculate PID output
            left_rpm, right_rpm = self.pid_control()
            
            # Send commands to ESP32
            self.send_motor_commands(left_rpm, right_rpm)
            
            # Debug info
            rospy.loginfo(f"Feedback - Left: {self.current_left_rpm:.1f} RPM, "
                         f"Right: {self.current_right_rpm:.1f} RPM | "
                         f"Pose: ({self.current_x:.2f}, {self.current_y:.2f}, "
                         f"{math.degrees(self.current_theta):.1f}°)")
            
            self.control_rate.sleep()

if __name__ == '__main__':
    try:
        controller = ROSPIDController()
        controller.run()
    except rospy.ROSInterruptException:
        pass