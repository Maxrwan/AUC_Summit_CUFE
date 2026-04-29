#!/usr/bin/env python3

import rospy
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Twist, Pose2D
import math

class ROSPIDController:
    def __init__(self):
        rospy.init_node('ros_pid_controller')
        
        self.motor_pub = rospy.Publisher('/motor_commands', Float32MultiArray, queue_size=10)
        self.cmd_vel_sub = rospy.Subscriber('/cmd_vel', Twist, self.cmd_vel_callback)
        
        # Robot parameters
        self.wheel_radius = 0.034  # meters
        self.wheel_distance = 0.18  # meters
        
        self.target_linear = 0.0
        self.target_angular = 0.0
        
        # PID variables
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
        
        self.control_rate = rospy.Rate(20)
        
        rospy.loginfo("ROS PID Controller Ready")
        
    def cmd_vel_callback(self, msg):
        self.target_linear = msg.linear.x
        self.target_angular = msg.angular.z
    
    def convert_to_rpm(self, linear, angular):
        left_speed = linear - angular * self.wheel_distance / 2
        right_speed = linear + angular * self.wheel_distance / 2
        
        left_rpm = (left_speed * 60.0) / (2 * math.pi * self.wheel_radius)
        right_rpm = (right_speed * 60.0) / (2 * math.pi * self.wheel_radius)
        
        return left_rpm, right_rpm
    
    def run(self):
        while not rospy.is_shutdown():
            left_rpm, right_rpm = self.convert_to_rpm(self.target_linear, self.target_angular)
            
            msg = Float32MultiArray()
            msg.data = [left_rpm, right_rpm]
            self.motor_pub.publish(msg)
            
            self.control_rate.sleep()

if __name__ == '__main__':
    try:
        controller = ROSPIDController()
        controller.run()
    except rospy.ROSInterruptException:
        pass
