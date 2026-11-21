"""Visual steering: turns /model/rover/cmd_vel into a steering angle for each wheel (4 servos).

Each wheel is pointed along the direction that wheel moves for the commanded motion:
    wheel velocity = (vx - w*y, vy + w*x)   with (x, y) = wheel position from the rover centre.
Angles are kept within +-90 deg (past that the wheel would simply run backwards).
Run by the launch file; or by hand:  python3 steer_node.py ~/olympus_ws/sim_models/rover_sim/urdf/rover_steer.json
"""
import json
import math
import os
import sys

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import Float64

DEFAULT_JSON = os.path.expanduser("~/olympus_ws/sim_models/rover_sim/urdf/rover_steer.json")


class SteerNode(Node):
    def __init__(self, path):
        super().__init__("steer_node")
        self.wheels = json.load(open(path))["wheels"]
        self.cmd = Twist()
        self.last = {w["steer_joint"]: 0.0 for w in self.wheels}
        self.pubs = {w["steer_joint"]: self.create_publisher(Float64, f"/model/rover/steer/{w['steer_joint']}", 10)
                     for w in self.wheels}
        self.create_subscription(Twist, "/model/rover/cmd_vel", self.on_cmd, 10)
        self.create_timer(0.05, self.tick)

    def on_cmd(self, msg):
        self.cmd = msg

    def tick(self):
        vx, vy, w = self.cmd.linear.x, self.cmd.linear.y, self.cmd.angular.z
        for wh in self.wheels:
            wx = vx - w * wh["y"]
            wy = vy + w * wh["x"]
            if math.hypot(wx, wy) > 1e-3:                    # when stopped, keep the last angle
                ang = math.atan2(wy, wx)
                if ang > math.pi / 2:
                    ang -= math.pi
                elif ang < -math.pi / 2:
                    ang += math.pi
                self.last[wh["steer_joint"]] = ang
            self.pubs[wh["steer_joint"]].publish(Float64(data=wh["sign"] * self.last[wh["steer_joint"]]))


def main():
    rclpy.init()
    node = SteerNode(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else DEFAULT_JSON)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
