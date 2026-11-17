#!/usr/bin/env python3
"""Bridge between a velocity command and the Drive_MCU board.

Listens to a velocity command (forward speed + turning speed), the same kind of
command the simulation's drive controller takes, and sends the 4 motor
percentages to the STM32 on /drive/motor_cmd (std_msgs/Int16MultiArray).

Robotone has fixed wheels (skid steering): to turn, the left and right sides
turn at different speeds.

    left  wheel speed = v - w * track_width / 2
    right wheel speed = v + w * track_width / 2
    percent           = wheel speed / max_wheel_speed * 100

Safety: if no velocity command arrives for cmd_timeout seconds, it sends 0.
The STM32 also stops by itself after 0.5 s without any /drive/motor_cmd.

Olympus MARS, 2026.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped
from std_msgs.msg import Int16MultiArray


class CmdVelToMotors(Node):
    def __init__(self):
        super().__init__('cmd_vel_to_motors')

        # Every parameter can be changed at start with: --ros-args -p name:=value
        self.declare_parameter('cmd_topic', '/cmd_vel')     # topic to listen to
        self.declare_parameter('stamped', False)            # True = TwistStamped, False = Twist
        self.declare_parameter('track_width', 0.30)         # m, left to right wheel centre (MEASURE IT)
        self.declare_parameter('max_wheel_speed', 0.50)     # m/s of a wheel at 100 % (MEASURE IT)
        self.declare_parameter('left_motors', [0, 1])       # motor indices 0..3 = M1..M4 on the left side
        self.declare_parameter('right_motors', [2, 3])      # motor indices on the right side
        self.declare_parameter('max_percent', 60)           # safety limit sent to the motors
        self.declare_parameter('cmd_timeout', 0.5)          # s without command -> send 0
        self.declare_parameter('rate', 20.0)                # Hz, how often we send to the MCU

        self.track = float(self.get_parameter('track_width').value)
        self.vmax = float(self.get_parameter('max_wheel_speed').value)
        self.left = [int(i) for i in self.get_parameter('left_motors').value]
        self.right = [int(i) for i in self.get_parameter('right_motors').value]
        self.max_pct = int(self.get_parameter('max_percent').value)
        self.timeout = float(self.get_parameter('cmd_timeout').value)
        topic = str(self.get_parameter('cmd_topic').value)
        stamped = bool(self.get_parameter('stamped').value)
        rate = float(self.get_parameter('rate').value)

        for i in self.left + self.right:
            if not 0 <= i <= 3:
                raise ValueError(f'motor index {i} is not between 0 and 3')
        if self.vmax <= 0.0:
            raise ValueError('max_wheel_speed must be > 0')

        if stamped:
            self.create_subscription(TwistStamped, topic, lambda m: self.on_cmd(m.twist), 10)
        else:
            self.create_subscription(Twist, topic, self.on_cmd, 10)
        self.pub = self.create_publisher(Int16MultiArray, '/drive/motor_cmd', 10)

        self.v = 0.0          # m/s forward
        self.w = 0.0          # rad/s, positive = turn left
        self.last_cmd = None  # time of the last velocity command
        self.create_timer(1.0 / rate, self.send)

        kind = 'TwistStamped' if stamped else 'Twist'
        self.get_logger().info(
            f'Listening to {topic} ({kind}), sending /drive/motor_cmd at {rate:.0f} Hz. '
            f'track_width={self.track} m, max_wheel_speed={self.vmax} m/s, '
            f'left={self.left}, right={self.right}, max_percent={self.max_pct}')

    def on_cmd(self, twist):
        self.v = twist.linear.x
        self.w = twist.angular.z
        self.last_cmd = self.get_clock().now()

    def to_percent(self, wheel_speed):
        pct = round(wheel_speed / self.vmax * 100.0)
        return max(-self.max_pct, min(self.max_pct, pct))

    def compute(self):
        """Return the 4 motor percentages for the latest command."""
        v, w = self.v, self.w
        if self.last_cmd is None:
            v = w = 0.0
        else:
            age = (self.get_clock().now() - self.last_cmd).nanoseconds * 1e-9
            if age > self.timeout:
                v = w = 0.0
        left_pct = self.to_percent(v - w * self.track / 2.0)
        right_pct = self.to_percent(v + w * self.track / 2.0)
        out = [0, 0, 0, 0]
        for i in self.left:
            out[i] = left_pct
        for i in self.right:
            out[i] = right_pct
        return out

    def send(self):
        msg = Int16MultiArray()
        msg.data = self.compute()
        self.pub.publish(msg)

    def stop(self):
        msg = Int16MultiArray()
        msg.data = [0, 0, 0, 0]
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = CmdVelToMotors()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()  # best effort; the MCU also stops after 0.5 s on its own
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
