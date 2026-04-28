import rclpy
from rclpy.node import Node
import numpy as np

from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Twist

from Processing import generate_trajectory


class ProcessingNode(Node):

    def __init__(self):
        super().__init__('processing_node')

        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/drawing_coords_raw',
            self.path_cb,
            10
        )

        self.publisher_ = self.create_publisher(
            Twist,
            '/ros_pid_controller',
            10
        )

        self.timer = None

        self.vx_all = []
        self.vy_all = []
        self.vz_all = []
        self.index = 0
        self.dt = 0.1

        self.get_logger().info("Processing node ready")

    def path_cb(self, msg):

        pts = np.array(msg.data).reshape(-1, 2)

        if len(pts) < 2:
            self.get_logger().warn("Not enough points")
            return

        self.get_logger().info(f"Received {len(pts)} points")

        vx_all, vy_all, vz_all, dt = generate_trajectory(pts)

        self.vx_all = vx_all
        self.vy_all = vy_all
        self.vz_all = vz_all
        self.dt = dt
        self.index = 0

        # stop old timer if exists
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

        self.timer = self.create_timer(self.dt, self.publish_velocity)

    def publish_velocity(self):

        if self.index >= len(self.vx_all):
            self.get_logger().info("Trajectory finished")
            self.timer.cancel()
            self.timer = None
            return

        msg = Twist()
        msg.linear.x = float(self.vx_all[self.index])
        msg.linear.y = float(self.vy_all[self.index])
        msg.linear.z = float(self.vz_all[self.index])

        self.publisher_.publish(msg)

        self.index += 1

def main(args=None):
    import rclpy
    rclpy.init(args=args)
    node = ProcessingNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()