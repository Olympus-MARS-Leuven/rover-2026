"""Five-joint controls, software travel limits, and non-blocking servo ramps."""

from dataclasses import dataclass
import time


@dataclass(frozen=True)
class Joint:
    name: str
    channel: int
    minimum: int
    maximum: int
    initial: int = 300


# Channels: backup webServer.py; limits: backup config.txt. These are initial
# software limits, not independently measured mechanical endpoints.
# Gripper tightened to 330 following the user's fully-closed test at that value.
JOINTS = {
    "camera": Joint("Camera tilt", 11, 201, 300),
    "lower": Joint("Lower arm", 12, 300, 430),
    "upper": Joint("Upper arm", 13, 139, 443),
    "wrist": Joint("Wrist rotation", 14, 300, 500),
    "gripper": Joint("Gripper", 15, 300, 330),
}


class SimulatedServos:
    hardware = False

    def __init__(self):
        self.outputs = {}

    def set_position(self, channel, ticks):
        self.outputs[channel] = ticks

    def release(self):
        self.outputs.clear()

    def close(self):
        self.release()


class HardwareServos:
    hardware = True

    def __init__(self):
        from smbus import SMBus
        from servo_probe import PCA9685Probe
        self.bus = SMBus(1)
        self.probe = PCA9685Probe(self.bus)
        self.closed = False
        try:
            self.probe.prepare()  # All outputs OFF; no initial position commands.
        except BaseException:
            self.close()
            raise

    def set_position(self, channel, ticks):
        if self.closed:
            raise RuntimeError("Servo driver is closed")
        self.probe.set_position(channel, ticks)

    def release(self):
        if not self.closed:
            self.probe.all_off()

    def close(self):
        if not self.closed:
            try:
                self.release()
            finally:
                self.closed = True
                self.bus.close()


class Arm:
    """Called under Controller.lock; the watchdog advances ramps at 50 Hz."""

    def __init__(self, driver, clock=time.monotonic):
        self.driver = driver
        self.clock = clock
        self.enabled = False
        self.positions = {key: float(j.initial) for key, j in JOINTS.items()}
        self.targets = self.positions.copy()
        self.active = set()
        self.sent = {}
        self.jog = {}
        self.speed = 100
        self.last_step = clock()

    def configure(self, data):
        if not isinstance(data, dict) or type(data.get("enabled")) is not bool:
            raise ValueError("Invalid arm command")
        speed = data.get("speed", 100)
        targets, jog = data.get("targets", {}), data.get("jog", {})
        deadman = data.get("deadman", False)
        hold = data.get("hold", False)
        if type(speed) not in (int, float) or not 25 <= speed <= 200:
            raise ValueError("Arm speed must be between 25 and 200")
        if (type(deadman) is not bool or type(hold) is not bool
                or not isinstance(targets, dict) or not isinstance(jog, dict)):
            raise ValueError("Invalid arm control values")
        for key, percent in targets.items():
            if key not in JOINTS or type(percent) not in (int, float) or not 0 <= percent <= 100:
                raise ValueError("Joint position must be between 0 and 100 percent")
        for key, direction in jog.items():
            if key not in JOINTS or type(direction) is not int or direction not in (-1, 1):
                raise ValueError("Invalid arm jogging direction")
        if len(jog) > 1:
            raise ValueError("Jog one joint at a time")
        if not data["enabled"]:
            self.release()
            return
        if not self.enabled:
            self.last_step = self.clock()
        self.enabled = True
        self.speed = speed  # 100% in UI = 100 PWM ticks/second.
        if hold:
            self.targets = self.positions.copy()
            self.jog.clear()
            return
        self.jog = jog.copy() if deadman else {}
        for key, percent in targets.items():
            joint = JOINTS[key]
            self.targets[key] = joint.minimum + percent / 100 * (joint.maximum - joint.minimum)
        for key in self.jog:
            self.targets[key] = self.positions[key]
        # Enabling alone sends no positions. Each joint starts only on first use.
        for key in set(targets) | set(self.jog):
            if key not in self.active:
                self._write(key)
                self.active.add(key)

    def _write(self, key):
        ticks = round(self.positions[key])
        if key not in self.active or self.sent.get(key) != ticks:
            self.driver.set_position(JOINTS[key].channel, ticks)
            self.sent[key] = ticks

    def step(self):
        now = self.clock()
        dt = min(max(now - self.last_step, 0), 0.1)
        self.last_step = now
        if not self.enabled:
            return
        for key in tuple(self.active):
            joint = JOINTS[key]
            if key in self.jog:
                value = self.positions[key] + self.jog[key] * self.speed * dt
                self.positions[key] = min(joint.maximum, max(joint.minimum, value))
                self.targets[key] = self.positions[key]
            else:
                delta = self.targets[key] - self.positions[key]
                distance = min(abs(delta), self.speed * dt)
                self.positions[key] += distance if delta > 0 else -distance
            self._write(key)

    def release(self):
        had_active = bool(self.active)
        self.enabled = False
        self.active.clear()
        self.jog.clear()
        self.targets = self.positions.copy()
        self.sent.clear()
        if had_active:
            self.driver.release()

    def status(self):
        joints = {}
        for key, joint in JOINTS.items():
            span = joint.maximum - joint.minimum
            joints[key] = {
                "name": joint.name, "channel": joint.channel,
                "minimum": joint.minimum, "maximum": joint.maximum,
                "ticks": round(self.positions[key]),
                "percent": round((self.positions[key] - joint.minimum) / span * 100, 1),
                "target": round((self.targets[key] - joint.minimum) / span * 100, 1),
                "active": key in self.active,
            }
        return {"enabled": self.enabled, "hardware": self.driver.hardware,
                "speed": self.speed, "joints": joints}

    def close(self):
        try:
            self.release()
        finally:
            self.driver.close()
