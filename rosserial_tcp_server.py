#!/usr/bin/env python3
"""
rosserial TCP server – allows multiple ESP32 boards to connect over WiFi.
Start this node before running your PID controller.
"""

import rospy
import socket
import threading
import sys
from rosserial_python import SerialRos

class TCPServer:
    def __init__(self, port=11411, address='0.0.0.0'):
        self.port = port
        self.address = address
        self.buffer_size = 4096
        self.sock = None
        self.clients = []
        self.running = False
        
    def start(self):
        rospy.init_node('rosserial_tcp_server', log_level=rospy.INFO)
        rospy.loginfo(f"Starting rosserial TCP server on {self.address}:{self.port} ...")
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.address, self.port))
        self.sock.listen(5)
        self.sock.settimeout(1.0)
        
        self.running = True
        rospy.loginfo("Server ready – waiting for ESP connections...")
        
        # Accept connections in a loop
        while self.running and not rospy.is_shutdown():
            try:
                client_socket, client_addr = self.sock.accept()
                rospy.loginfo(f"✅ Client connected: {client_addr[0]}:{client_addr[1]}")
                
                # Create a SerialRos instance for this client
                serial_ros = SerialRos(
                    port=client_addr[0],
                    baudrate=None,
                    protocol='socket',
                    client_socket=client_socket
                )
                
                # Start in a new thread
                thread = threading.Thread(target=self.handle_client, args=(serial_ros, client_addr))
                thread.daemon = True
                thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    rospy.logerr(f"Accept error: {e}")
        
        self.cleanup()
    
    def handle_client(self, serial_ros, client_addr):
        """Handle a single ESP32 connection using SerialRos"""
        try:
            rospy.loginfo(f"Starting serial ROS handler for {client_addr[0]}")
            serial_ros.spin()
        except Exception as e:
            rospy.logerr(f"Client {client_addr[0]} error: {e}")
        finally:
            rospy.loginfo(f"❌ Client disconnected: {client_addr[0]}")
    
    def cleanup(self):
        self.running = False
        if self.sock:
            self.sock.close()
        rospy.loginfo("TCP server shut down")

if __name__ == '__main__':
    try:
        port = rospy.get_param('~port', 11411)
        address = rospy.get_param('~address', '0.0.0.0')
        server = TCPServer(port=port, address=address)
        server.start()
    except rospy.ROSInterruptException:
        pass