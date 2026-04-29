#!/usr/bin/env python3

import rospy
from std_msgs.msg import String, Int32, Float32MultiArray
from geometry_msgs.msg import Pose2D
import sys

class CommunicationTester:
    def __init__(self):
        rospy.init_node('communication_tester', anonymous=True)
        
        # Publishers for ESP32
        self.esp32_cmd_pub = rospy.Publisher('/esp32_command', String, queue_size=10)
        self.motor_cmd_pub = rospy.Publisher('/motor_commands', Float32MultiArray, queue_size=10)
        
        # Subscribers from ESP32
        self.debug_sub = rospy.Subscriber('/esp32_debug', String, self.debug_callback)
        self.heartbeat_sub = rospy.Subscriber('/esp32_heartbeat', Int32, self.heartbeat_callback)
        self.encoder_sub = rospy.Subscriber('/motor_encoders', Float32MultiArray, self.encoder_callback)
        self.pose_sub = rospy.Subscriber('/robot_pose', Pose2D, self.pose_callback)
        
        rospy.loginfo("=" * 60)
        rospy.loginfo("ATOM PnP - Communication Tester Started")
        rospy.loginfo("=" * 60)
        rospy.loginfo("Listening to:")
        rospy.loginfo("  - /esp32_debug (String)")
        rospy.loginfo("  - /esp32_heartbeat (Int32)")
        rospy.loginfo("  - /motor_encoders (Float32MultiArray)")
        rospy.loginfo("  - /robot_pose (Pose2D)")
        rospy.loginfo("")
        rospy.loginfo("Publishing to:")
        rospy.loginfo("  - /esp32_command (String)")
        rospy.loginfo("  - /motor_commands (Float32MultiArray)")
        rospy.loginfo("=" * 60)
    
    def debug_callback(self, msg):
        rospy.loginfo("[ESP32 DEBUG]: {}".format(msg.data))
    
    def heartbeat_callback(self, msg):
        rospy.loginfo_throttle(5, "[HEARTBEAT]: Count = {}".format(msg.data))
    
    def encoder_callback(self, msg):
        if len(msg.data) >= 4:
            rospy.loginfo_throttle(2, 
                "[ENCODERS]: L_RPM={:.2f}, R_RPM={:.2f}, L_Count={}, R_Count={}".format(
                    msg.data[0], msg.data[1], int(msg.data[2]), int(msg.data[3])))
    
    def pose_callback(self, msg):
        rospy.loginfo_throttle(2, 
            "[POSE]: x={:.3f}, y={:.3f}, theta={:.2f}".format(msg.x, msg.y, msg.theta))
    
    def send_test_messages(self):
        test_messages = [
            "Hello ESP32! Test message 1",
            "Communication check from ROS",
            "If you see this, we're connected!",
            "Testing bidirectional communication",
            "ATOM PnP system online",
        ]
        
        rate = rospy.Rate(0.5)
        
        for msg_text in test_messages:
            if not rospy.is_shutdown():
                msg = String()
                msg.data = msg_text
                self.esp32_cmd_pub.publish(msg)
                rospy.loginfo("[SENT]: {}".format(msg_text))
                rate.sleep()
        
        rospy.loginfo("Test messages sent! Check ESP32 serial monitor.")
    
    def send_motor_commands(self, left_rpm=50.0, right_rpm=50.0):
        msg = Float32MultiArray()
        msg.data = [left_rpm, right_rpm]
        self.motor_cmd_pub.publish(msg)
        rospy.loginfo("[MOTOR CMD]: Left={} RPM, Right={} RPM".format(left_rpm, right_rpm))
    
    def run_test_sequence(self):
        rospy.loginfo("\n=== Starting Test Sequence ===\n")
        
        rospy.sleep(2)
        
        rospy.loginfo("Test 1: Sending debug messages...")
        self.send_test_messages()
        
        rospy.sleep(2)
        
        rospy.loginfo("Test 2: Sending motor commands...")
        for speed in [25, 50, 75, 100]:
            self.send_motor_commands(speed, speed)
            rospy.sleep(2)
        
        rospy.loginfo("Test 3: Stopping motors...")
        self.send_motor_commands(0, 0)
        
        rospy.loginfo("=== Test Sequence Complete ===")

if __name__ == '__main__':
    try:
        tester = CommunicationTester()
        
        if len(sys.argv) > 1 and sys.argv[1] == "auto":
            tester.run_test_sequence()
        else:
            rospy.loginfo("\nInteractive mode. Press Ctrl+C to exit.")
            rospy.loginfo("Use 'auto' argument for automated test")
            rospy.spin()
            
    except rospy.ROSInterruptException:
        pass
