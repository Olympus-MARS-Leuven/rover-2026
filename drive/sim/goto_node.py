"""ROS 2 node: drive the rover to a list of (x, y) coordinates.

Default setup (the Olympus rover in Gazebo, through ros_gz_bridge):
  position in:  /model/rover/odometry   (nav_msgs/Odometry)  -> x forward, y left, starts at 0,0 at spawn
  commands out: /model/rover/cmd_vel    (geometry_msgs/Twist)

Other setups by parameter:
  -p pose_type:=posearray -p pose_topic:=/world/empty/dynamic_pose/info   (Gazebo ground truth, like measure_pose.py)
  -p stamped:=true -p cmd_topic:=/diff_drive_controller/cmd_vel            (TwistStamped, like demo_drive.py)

Run:
  python3 goto_node.py --ros-args -p waypoints:="[1.0, 0.0, 1.0, 1.0]"
"""
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseArray, Twist, TwistStamped
from nav_msgs.msg import Odometry

try:
    from .goto_controller import GoToPoint        # when installed as part of a package
except ImportError:
    from goto_controller import GoToPoint         # when run as a plain script


def yaw_from_quaternion(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class GoToNode(Node):
    def __init__(self):
        super().__init__("goto_node")

        self.declare_parameter("waypoints", [1.0, 0.0])       # x1, y1, x2, y2, ... in metres
        self.declare_parameter("relative_to_start", False)    # True: measured from the start pose
        self.declare_parameter("pose_type", "odom")           # "odom" (Odometry) or "posearray"
        self.declare_parameter("pose_topic", "/model/rover/odometry")
        self.declare_parameter("pose_index", 0)               # only for posearray: index of the rover in the array
        self.declare_parameter("cmd_topic", "/model/rover/cmd_vel")
        self.declare_parameter("stamped", False)              # True: publish TwistStamped instead of Twist
        self.declare_parameter("v_max", 0.2)
        self.declare_parameter("w_max", 0.5)

        flat = list(self.get_parameter("waypoints").value)
        if len(flat) % 2 != 0 or not flat:
            raise ValueError("waypoints must be x1,y1,x2,y2,... (an even number of values)")
        self.raw_waypoints = [(flat[i], flat[i + 1]) for i in range(0, len(flat), 2)]
        self.relative = self.get_parameter("relative_to_start").value
        self.index = self.get_parameter("pose_index").value

        self.controller = None            # created when the first pose arrives
        self.pose = None                  # (x, y, yaw)
        self.pose_time = None

        self.pose_type = self.get_parameter("pose_type").value
        msg_type = Odometry if self.pose_type == "odom" else PoseArray
        self.create_subscription(msg_type, self.get_parameter("pose_topic").value, self.on_pose, 10)
        self.stamped = self.get_parameter("stamped").value
        self.pub = self.create_publisher(TwistStamped if self.stamped else Twist,
                                         self.get_parameter("cmd_topic").value, 10)
        self.create_timer(0.05, self.on_timer)        # 20 Hz, also while stopped
        self.get_logger().info(f"waiting for pose, {len(self.raw_waypoints)} waypoint(s) loaded")

    def on_pose(self, msg):
        p = msg.pose.pose if self.pose_type == "odom" else msg.poses[self.index]
        x, y, yaw = p.position.x, p.position.y, yaw_from_quaternion(p.orientation)
        self.pose = (x, y, yaw)
        self.pose_time = self.get_clock().now()

        if self.controller is None:
            wps = self.raw_waypoints
            if self.relative:
                # turn start-frame coordinates into world coordinates
                c, s = math.cos(yaw), math.sin(yaw)
                wps = [(x + c * px - s * py, y + s * px + c * py) for px, py in wps]
            self.controller = GoToPoint(
                wps,
                v_max=self.get_parameter("v_max").value,
                w_max=self.get_parameter("w_max").value)
            self.get_logger().info(
                f"start pose ({x:.2f}, {y:.2f}, yaw {yaw:.2f}); world targets: "
                + ", ".join(f"({a:.2f}, {b:.2f})" for a, b in wps))

    def on_timer(self):
        lin = ang = 0.0
        fresh = (self.pose_time is not None and
                 (self.get_clock().now() - self.pose_time).nanoseconds < 0.5e9)
        if self.controller is not None and fresh:           # no fresh pose -> send zeros
            lin, ang, event = self.controller.step(*self.pose)
            if event:
                self.get_logger().info(event)
                if self.controller.done:
                    self.get_logger().info("all waypoints reached, holding still")

        self.pub.publish(self.make_cmd(lin, ang))

    def make_cmd(self, lin, ang):
        if self.stamped:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.twist.linear.x = lin
            msg.twist.angular.z = ang
        else:
            msg = Twist()
            msg.linear.x = lin
            msg.angular.z = ang
        return msg


def main():
    rclpy.init()
    node = GoToNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.pub.publish(node.make_cmd(0.0, 0.0))   # last message is always a stop
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
