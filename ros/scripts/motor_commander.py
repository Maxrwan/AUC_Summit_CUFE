#!/usr/bin/env python3

import rospy
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Twist

class MotorCommander:
    def __init__(self):
        rospy.init_node('motor_commander', anonymous=True)
        
        self.motor_pub = rospy.Publisher('/motor_commands', Float32MultiArray, queue_size=10)
        self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        
        rospy.loginfo("Motor Commander Ready")
        rospy.loginfo("Commands: STOP, FORWARD, BACKWARD, LEFT, RIGHT, or RPMs (l r)")
    
    def send_command(self, left_rpm, right_rpm):
        msg = Float32MultiArray()
        msg.data = [float(left_rpm), float(right_rpm)]
        self.motor_pub.publish(msg)
        rospy.loginfo("Motors: Left={:.1f} RPM, Right={:.1f} RPM".format(left_rpm, right_rpm))
    
    def run(self):
        rospy.loginfo("Type command and press Enter. 'q' to quit.")
        rospy.loginfo("Examples: forward, 50 50, stop")
        
        while not rospy.is_shutdown():
            try:
                cmd = raw_input("\nEnter command: ").strip().upper()
                
                if cmd == 'Q':
                    self.send_command(0, 0)
                    break
                elif cmd == 'STOP':
                    self.send_command(0, 0)
                elif cmd == 'FORWARD':
                    self.send_command(50, 50)
                elif cmd == 'BACKWARD':
                    self.send_command(-50, -50)
                elif cmd == 'LEFT':
                    self.send_command(-30, 30)
                elif cmd == 'RIGHT':
                    self.send_command(30, -30)
                else:
                    try:
                        values = cmd.split()
                        if len(values) == 2:
                            left, right = float(values[0]), float(values[1])
                            self.send_command(left, right)
                        else:
                            rospy.logwarn("Need 2 values or a command")
                    except ValueError:
                        rospy.logwarn("Invalid input. Use numbers or commands.")
                        
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        self.send_command(0, 0)
        rospy.loginfo("Motors stopped. Exiting.")

if __name__ == '__main__':
    try:
        commander = MotorCommander()
        commander.run()
    except rospy.ROSInterruptException:
        pass
