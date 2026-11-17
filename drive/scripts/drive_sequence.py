#!/usr/bin/env python3
"""Predefined drive movement: forward, stop, turn, stop.

Publishes velocity commands (forward speed + turning speed) at 20 Hz.
The same script can drive:
  - the real Robotone, through cmd_vel_to_motors.py and the Drive_MCU board;
  - the simulation, by sending to the simulation's controller topic.

Examples:
  python3 drive_sequence.py
  python3 drive_sequence.py --ros-args -p cmd_topic:=/diff_drive_controller/cmd_vel -p stamped:=true

Olympus MARS, 2026.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped

# (forward speed m/s, turning speed rad/s, duration s). Positive turn = to the left.
SEQUENCE = [
    (0.20, 0.0, 2.0),   # forward
    (0.00, 0.0, 1.0),   # stop
    (0.00, 1.0, 1.5),   # turn left on the spot
    (0.00, 0.0, 1.0),   # stop
    (-0.20, 0.0, 2.0),  # backward
    (0.00, 0.0, 1.0),   # stop
]
RATE_HZ = 20.0


class DriveSequence(Node):
    def __init__(self):
        super().__init__('drive_sequence')
        self.declare_parameter('cmd_topic', '/cmd_vel')
        self.declare_parameter('stamped', False)
        self.declare_parameter('frame_id', 'base_link')
        topic = str(self.get_parameter('cmd_topic').value)
        self.stamped = bool(self.get_parameter('stamped').value)
        self.frame_id = str(self.get_parameter('frame_id').value)
        msg_type = TwistStamped if self.stamped else Twist
        self.pub = self.create_publisher(msg_type, topic, 10)

        self.step = 0
        self.step_start = None
        self.timer = self.create_timer(1.0 / RATE_HZ, self.tick)
        self.done = False
        self.get_logger().info(f'Sending the sequence on {topic} '
                               f'({"TwistStamped" if self.stamped else "Twist"})')

    def publish(self, v, w):
        twist = Twist()
        twist.linear.x = float(v)
        twist.angular.z = float(w)
        if self.stamped:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = self.frame_id
            msg.twist = twist
            self.pub.publish(msg)
        else:
            self.pub.publish(twist)

    def tick(self):
        now = self.get_clock().now()
        if self.step_start is None:
            self.step_start = now
            v, w, d = SEQUENCE[self.step]
            self.get_logger().info(f'Step {self.step}: v={v} m/s, w={w} rad/s for {d} s')
        v, w, duration = SEQUENCE[self.step]
        if (now - self.step_start).nanoseconds * 1e-9 >= duration:
            self.step += 1
            self.step_start = None
            if self.step >= len(SEQUENCE):
                self.publish(0.0, 0.0)
                self.get_logger().info('Sequence done')
                self.done = True
            return
        self.publish(v, w)


def main():
    rclpy.init()
    node = DriveSequence()
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        node.publish(0.0, 0.0)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
