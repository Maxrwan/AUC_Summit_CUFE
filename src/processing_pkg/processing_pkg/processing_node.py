import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ProcessingNode(Node):
    def __init__(self):
        super().__init__('processing_node')  # ✅ REQUIRED

        self.publisher_ = self.create_publisher(String, 'processing_node', 10)
        self.timer = self.create_timer(10.0, self.publish_message)

        self.get_logger().info("Processing node started")

    def publish_message(self):
        msg = String()
        msg.data = "Marwan"
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published: "{msg.data}"')


def main(args=None):
    rclpy.init(args=args)
    node = ProcessingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
