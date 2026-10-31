"""Five-joint controls, software travel limits, and non-blocking servo ramps."""

from dataclasses import dataclass
import math
import time

from calibration import GLOBAL_MAX, GLOBAL_MIN, LABELS


@dataclass(frozen=True)
class Joint:
    name: str
    channel: int
    minimum: int
    maximum: int
    # Joints that sag to the same resting pose when their signal is removed.
    gravity: bool = False
    initial: int = 300


# Channels: backup webServer.py; limits: backup config.txt. These are initial
# software limits, not independently measured mechanical endpoints.
# Gripper tightened to 330 following the user's fully-closed test at that value.
# Measured values from calibration.json replace them (see calibration.py).
JOINTS = {
    "camera": Joint("Camera tilt", 11, 201, 300),
    "lower": Joint("Lower arm", 12, 300, 430, gravity=True),
    "upper": Joint("Upper arm", 13, 139, 443, gravity=True),
    "wrist": Joint("Wrist rotation", 14, 300, 500),
    "gripper": Joint("Gripper", 15, 300, 330),
}
HOLD_AFTER_STOP = 10.0     # Seconds a frozen arm keeps holding before release.
CALIBRATION_SPEED = 40     # Ticks/second cap while searching for limits.
ACTIVATION_GAP = 0.3       # Seconds between powering joints, to limit current peaks.


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


def _ratio(value):
    """Jog rates are -1..1; keyboard sends -1/1, a stick anything between."""
    return type(value) in (int, float) and math.isfinite(value) and -1 <= value <= 1


class Arm:
    """Called under Controller.lock; the watchdog advances ramps at 50 Hz."""

    def __init__(self, driver, clock=time.monotonic, calibration=None, remembered=None, on_release=None):
        self.driver = driver
        self.clock = clock
        self.on_release = on_release
        self.enabled = False
        self.calibrating = False
        self.frozen_at = None
        self.active = set()
        self.sent = {}
        self.jog = {}
        self.pending = []
        self.next_activation = 0.0
        self.speed = 100
        self.last_step = clock()
        self.apply_calibration(calibration or {}, remembered or {})

    def check_calibration(self, joints):
        """Changing a servo channel while powered would move the wrong joint."""
        channels = {key: joints.get(key, {}).get("channel", j.channel) for key, j in JOINTS.items()}
        if self.active and channels != getattr(self, "channels", channels):
            raise ValueError("Release the arm before changing servo channels")

    def apply_calibration(self, joints, remembered=None):
        """Use measured channels, limits, directions and rest poses."""
        self.check_calibration(joints)
        self.calibration = {key: dict(joints.get(key, {})) for key in JOINTS}
        self.channels, self.limits, self.labels, self.rest = {}, {}, {}, {}
        for key, joint in JOINTS.items():
            data = self.calibration[key]
            self.channels[key] = data.get("channel", joint.channel)
            self.limits[key] = (data.get("minimum", joint.minimum), data.get("maximum", joint.maximum))
            negative, positive = LABELS[key]
            if data.get("positive", positive) != positive:
                negative, positive = positive, negative
            self.labels[key] = (negative, positive)
            if "rest" in data:
                self.rest[key] = data["rest"]
        if self.active:
            return  # Powered joints keep their positions; only limits and labels change.
        if remembered is None:  # New calibration while running: keep what is known.
            remembered = {k: round(v) for k, v in self.positions.items()
                          if self.start_source[k] == "remembered"}
            previous = self.positions
        else:
            previous = {}
        self.positions, self.start_source = {}, {}
        for key, joint in JOINTS.items():
            # A sagging joint ends at its rest pose; others stay where they were left.
            if joint.gravity and key in self.rest:
                value, source = self.rest[key], "rest"
            elif not joint.gravity and key in remembered:
                value, source = remembered[key], "remembered"
            elif key in self.rest:
                value, source = self.rest[key], "rest"
            else:
                value, source = previous.get(key, joint.initial), "unknown"
            self.positions[key] = float(value)
            self.start_source[key] = source
        self.targets = self.positions.copy()

    def known_start(self, key):
        return self.start_source[key] != "unknown"

    def configure(self, data):
        if not isinstance(data, dict) or type(data.get("enabled")) is not bool:
            raise ValueError("Invalid arm command")
        speed = data.get("speed", 100)
        targets, jog, ticks = data.get("targets", {}), data.get("jog", {}), data.get("ticks", {})
        flags = {name: data.get(name, False) for name in ("deadman", "hold", "release", "calibrate", "park")}
        if type(speed) not in (int, float) or not 25 <= speed <= 200:
            raise ValueError("Arm speed must be between 25 and 200")
        if (any(type(value) is not bool for value in flags.values())
                or not all(isinstance(v, dict) for v in (targets, jog, ticks))):
            raise ValueError("Invalid arm control values")
        for key, percent in targets.items():
            if key not in JOINTS or type(percent) not in (int, float) or not 0 <= percent <= 100:
                raise ValueError("Joint position must be between 0 and 100 percent")
        for key, rate in jog.items():
            if key not in JOINTS or not _ratio(rate):
                raise ValueError("Invalid arm jogging direction")
        for key, value in ticks.items():
            if key not in JOINTS or type(value) is not int or not GLOBAL_MIN <= value <= GLOBAL_MAX:
                raise ValueError(f"Calibration ticks must be whole numbers within {GLOBAL_MIN}-{GLOBAL_MAX}")
        if ticks and not flags["calibrate"]:
            raise ValueError("Absolute ticks are only accepted in calibration mode")
        if flags["release"]:
            self.release()
            return
        if not data["enabled"]:
            self.freeze()
            return
        now = self.clock()
        if not self.enabled:
            self.last_step = now
            self.next_activation = now
            # With a trustworthy start estimate, power all joints so none flops.
            # Calibration powers only the joint under test.
            self.pending = [] if flags["calibrate"] else [
                k for k in JOINTS if k not in self.active and self.known_start(k)]
        self.enabled = True
        self.frozen_at = None
        self.calibrating = flags["calibrate"]
        self.speed = min(speed, CALIBRATION_SPEED) if self.calibrating else speed
        if flags["hold"]:
            self.targets = self.positions.copy()
            self.jog.clear()
            return
        self.jog = {k: v for k, v in jog.items() if v} if flags["deadman"] else {}
        used = set(targets) | set(self.jog) | set(ticks)
        for key, percent in targets.items():
            low, high = self.limits[key]
            self.targets[key] = low + percent / 100 * (high - low)
        for key, value in ticks.items():
            if key not in self.active:
                self.positions[key] = float(value)  # Calibration: power the joint at this value.
            self.targets[key] = float(value)
        if flags["park"]:
            for key, value in self.rest.items():
                self.targets[key] = float(value)
                used.add(key)
        for key in self.jog:
            self.targets[key] = self.positions[key]
        for key in used:
            self._activate(key)

    def _activate(self, key):
        if key in self.pending:
            self.pending.remove(key)
        if key not in self.active:
            self.active.add(key)
            self._write(key)

    def _write(self, key):
        ticks = round(self.positions[key])
        if self.sent.get(key) != ticks:
            self.driver.set_position(self.channels[key], ticks)
            self.sent[key] = ticks

    def _bounds(self, key):
        return (GLOBAL_MIN, GLOBAL_MAX) if self.calibrating else self.limits[key]

    def step(self):
        now = self.clock()
        dt = min(max(now - self.last_step, 0), 0.1)
        self.last_step = now
        if self.frozen_at is not None and now - self.frozen_at >= HOLD_AFTER_STOP:
            self.release()
            return
        if not self.enabled:
            return
        if self.pending and now >= self.next_activation:
            self._activate(self.pending[0])
            self.next_activation = now + ACTIVATION_GAP
        for key in tuple(self.active):
            low, high = self._bounds(key)
            position = self.positions[key]
            if key in self.jog:
                value = position + self.jog[key] * self.speed * dt
                # Never jump: a start outside the limits may only move back towards them.
                self.positions[key] = min(max(high, position), max(min(low, position), value))
                self.targets[key] = self.positions[key]
            else:
                # Targets are validated when set: sliders within limits, ticks
                # and rest poses within the absolute bounds.
                delta = self.targets[key] - position
                distance = min(abs(delta), self.speed * dt)
                self.positions[key] += distance if delta > 0 else -distance
            self._write(key)

    def freeze(self):
        """Stop moving but keep holding; the watchdog releases after HOLD_AFTER_STOP."""
        self.enabled = False
        self.calibrating = False
        self.jog.clear()
        self.pending.clear()
        self.targets = self.positions.copy()
        if self.active and self.frozen_at is None:
            self.frozen_at = self.clock()

    def release(self):
        had_active = bool(self.active)
        if had_active and self.on_release is not None:
            self.on_release({key: self.sent[key] for key in self.active if key in self.sent})
        self.enabled = False
        self.calibrating = False
        self.frozen_at = None
        for key in self.active:
            if JOINTS[key].gravity:
                if key in self.rest:
                    self.positions[key] = float(self.rest[key])
                else:
                    self.start_source[key] = "unknown"  # It sags somewhere unmeasured.
            else:
                self.start_source[key] = "remembered"
        self.active.clear()
        self.jog.clear()
        self.pending.clear()
        self.targets = self.positions.copy()
        self.sent.clear()
        if had_active:
            self.driver.release()

    def status(self):
        joints = {}
        for key, joint in JOINTS.items():
            low, high = self.limits[key]
            span = high - low
            joints[key] = {
                "name": joint.name, "channel": self.channels[key],
                "minimum": low, "maximum": high, "default_minimum": joint.minimum,
                "default_maximum": joint.maximum, "labels": list(self.labels[key]),
                "gravity": joint.gravity, "rest": self.rest.get(key),
                "start": self.start_source[key],
                "ticks": round(self.positions[key]),
                "percent": round((self.positions[key] - low) / span * 100, 1),
                "target": round((self.targets[key] - low) / span * 100, 1),
                "active": key in self.active,
            }
        holding = None
        if self.frozen_at is not None:
            holding = round(max(0.0, HOLD_AFTER_STOP - (self.clock() - self.frozen_at)), 1)
        return {"enabled": self.enabled, "hardware": self.driver.hardware,
                "speed": self.speed, "calibrating": self.calibrating,
                "release_in": holding, "joints": joints}

    def close(self):
        try:
            self.release()
        finally:
            self.driver.close()
