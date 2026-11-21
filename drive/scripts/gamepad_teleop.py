#!/usr/bin/env python3
"""Gamepad -> velocity command, with safety.

Reads sensor_msgs/Joy (from `ros2 run joy joy_node`) and publishes a
geometry_msgs/Twist at a fixed rate (default 20 Hz) on /cmd_vel, which
cmd_vel_to_motors.py turns into motor percentages.

Safety:
  - Deadman button: the robot only moves while it is HELD. Released = zero.
  - Watchdog: no Joy message for joy_timeout seconds (gamepad unplugged,
    joy_node stopped, link lost) = zero. The last command is never kept.
  - Speed limits are parameters, and are also capped by hard limits in this
    file, so a typo in a parameter cannot ask for a fast robot.
  - Switching drive/arm mode sends zero and needs the deadman to be released
    and pressed again before anything moves.
  - Zero is sent on shutdown. (cmd_vel_to_motors.py and the MCU also stop the
    motors after 0.5 s without commands.)

Button and axis numbers depend on the gamepad and on joy_node. The defaults
below are GUESSES. Check them with `ros2 topic echo /joy` while you press.

Olympus MARS, 2026.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy

HARD_MAX_LINEAR = 0.5    # m/s, never exceeded whatever the parameters say
HARD_MAX_ANGULAR = 1.0   # rad/s


def clamp(x, low, high):
    return max(low, min(high, x))


def apply_deadzone(x, zone):
    return 0.0 if abs(x) < zone else x


def pick(seq, i, default=0.0):
    """seq[i], or default when the index does not exist."""
    return seq[i] if 0 <= i < len(seq) else default


class GamepadTeleop(Node):
    def __init__(self):
        super().__init__('gamepad_teleop')

        self.declare_parameter('cmd_topic', '/cmd_vel')
        self.declare_parameter('max_linear', 0.2)       # m/s at full stick (start low)
        self.declare_parameter('max_angular', 0.5)      # rad/s at full stick
        self.declare_parameter('axis_linear', 1)        # forward/back stick axis (CHECK)
        self.declare_parameter('axis_angular', 0)       # left/right stick axis (CHECK)
        self.declare_parameter('invert_linear', False)  # True if stick up gives a negative number
        self.declare_parameter('invert_angular', False) # True if stick left gives a negative number
        self.declare_parameter('deadman_button', 9)     # hold to drive (CHECK)
        self.declare_parameter('mode_button', 6)        # press to switch drive <-> arm (CHECK)
        self.declare_parameter('deadzone', 0.1)
        self.declare_parameter('joy_timeout', 0.3)      # s without a Joy message -> zero
        self.declare_parameter('rate', 20.0)            # Hz

        p = self.get_parameter
        self.max_lin = clamp(float(p('max_linear').value), 0.0, HARD_MAX_LINEAR)
        self.max_ang = clamp(float(p('max_angular').value), 0.0, HARD_MAX_ANGULAR)
        self.ax_lin = int(p('axis_linear').value)
        self.ax_ang = int(p('axis_angular').value)
        self.sign_lin = -1.0 if bool(p('invert_linear').value) else 1.0
        self.sign_ang = -1.0 if bool(p('invert_angular').value) else 1.0
        self.btn_dead = int(p('deadman_button').value)
        self.btn_mode = int(p('mode_button').value)
        self.zone = float(p('deadzone').value)
        self.timeout = float(p('joy_timeout').value)
        topic = str(p('cmd_topic').value)
        rate = float(p('rate').value)

        if self.timeout <= 0.0 or rate <= 0.0:
            raise ValueError('joy_timeout and rate must be > 0')

        self.pub = self.create_publisher(Twist, topic, 10)
        self.create_subscription(Joy, '/joy', self.on_joy, 10)

        self.joy = None            # latest Joy message
        self.last_joy = None       # time it arrived
        self.arm_mode = False
        self.mode_was_pressed = False
        self.need_release = False  # after a mode switch: release the deadman first
        self.stale = True          # True while there is no fresh Joy (to log once)
        self.create_timer(1.0 / rate, self.tick)

        self.get_logger().info(
            f'Publishing {topic} at {rate:.0f} Hz. Limits: {self.max_lin} m/s, '
            f'{self.max_ang} rad/s. Hold button {self.btn_dead} to drive, '
            f'button {self.btn_mode} switches drive/arm. Mode: DRIVE')

    def on_joy(self, msg):
        self.joy = msg
        self.last_joy = self.get_clock().now()
        pressed = pick(msg.buttons, self.btn_mode, 0) == 1
        if pressed and not self.mode_was_pressed:      # button just pressed
            self.arm_mode = not self.arm_mode
            self.need_release = True
            self.get_logger().info(f'Mode: {"ARM" if self.arm_mode else "DRIVE"}')
        self.mode_was_pressed = pressed

    def compute(self):
        """Return (v, w) for now. (0, 0) in every doubtful case."""
        if self.joy is None or self.last_joy is None:
            return 0.0, 0.0
        age = (self.get_clock().now() - self.last_joy).nanoseconds * 1e-9
        if age > self.timeout:
            if not self.stale:
                self.get_logger().warn(f'No gamepad data for {age:.2f} s: sending zero')
                self.stale = True
            return 0.0, 0.0
        if self.stale:
            self.get_logger().info('Gamepad data is back')
            self.stale = False

        axes, buttons = self.joy.axes, self.joy.buttons
        if pick(buttons, self.btn_dead, 0) != 1:       # deadman not held
            self.need_release = False
            return 0.0, 0.0
        if self.need_release:
            return 0.0, 0.0

        if self.arm_mode:
            self.arm_tick(axes)
            return 0.0, 0.0                            # the wheels stay still in arm mode

        lin = clamp(apply_deadzone(pick(axes, self.ax_lin), self.zone), -1.0, 1.0)
        ang = clamp(apply_deadzone(pick(axes, self.ax_ang), self.zone), -1.0, 1.0)
        return self.sign_lin * lin * self.max_lin, self.sign_ang * ang * self.max_ang

    def arm_tick(self, axes):
        """Placeholder: send the sticks to the arm here once its topic is agreed."""
        self.get_logger().warn('Arm mode: not implemented yet', throttle_duration_sec=2.0)

    def publish(self, v, w):
        msg = Twist()
        msg.linear.x = float(v)
        msg.angular.z = float(w)
        self.pub.publish(msg)

    def tick(self):
        v, w = self.compute()
        self.publish(v, w)

    def stop(self):
        self.publish(0.0, 0.0)


def main():
    rclpy.init()
    node = GamepadTeleop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.stop()  # best effort; the bridge and the MCU also stop after 0.5 s
        except Exception:
            pass
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
