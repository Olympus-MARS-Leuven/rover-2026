"""Track driver and expiring control sessions. No hardware is opened on import."""

import secrets
import threading
import time


# BCM numbering from this robot's original move.py; A is right, B is left.
# Forward polarity selected from the latest report that all directions are reversed.
TRACKS = ((17, 27, 18, (1, 0)), (4, 14, 15, (0, 1)))  # left, right
MOTIONS = {
    "stop": (0, 0), "forward": (1, 1), "backward": (-1, -1),
    "left": (-1, 1), "right": (1, -1),
}
TIMEOUT = 2.0
DEFAULT_SPEED = 0.50
MAX_SPEED = 1.0


class ControlError(ValueError):
    """The browser must reconnect before it can drive again."""


class SimulatedMotors:
    def __init__(self):
        self.value = (0.0, 0.0)

    def set(self, left, right):
        self.value = (left, right)

    def close(self):
        self.set(0, 0)


class GPIOMotors:
    """Adeept green Motor Shield V2, Pi 3B. Servos are never touched."""

    def __init__(self, gpio=None, sleep=time.sleep):
        if gpio is None:
            import RPi.GPIO as gpio
        self.gpio = gpio
        self.sleep = sleep
        self.pwm = []
        self.pins = []
        self.value = (0.0, 0.0)
        self.last_sign = [0, 0]
        self.closed = False
        gpio.setmode(gpio.BCM)
        try:
            # Disable BOTH bridges before configuring their direction pins.
            for enable, _, _, _ in TRACKS:
                gpio.setup(enable, gpio.OUT, initial=gpio.LOW)
                self.pins.append(enable)
            for enable, pin1, pin2, _ in TRACKS:
                for pin in (pin1, pin2):
                    gpio.setup(pin, gpio.OUT, initial=gpio.LOW)
                    self.pins.append(pin)
                pwm = gpio.PWM(enable, 1000)
                self.pwm.append(pwm)
                pwm.start(0)
        except Exception:
            self.close()
            raise

    def set(self, left, right):
        if self.closed:
            raise RuntimeError("Motor driver is closed")
        values = (left, right)
        if any(not -MAX_SPEED <= value <= MAX_SPEED for value in values):
            raise ValueError("Motor duty must be between -100% and 100%")
        if values == self.value:
            return
        signs = [1 if v > 0 else -1 if v < 0 else 0 for v in values]
        for pwm in self.pwm:
            pwm.ChangeDutyCycle(0)
        # A short coast interval before reversing either track.
        if any(old * new < 0 for old, new in zip(self.last_sign, signs)):
            self.sleep(0.05)
        for i, (_, pin1, pin2, forward) in enumerate(TRACKS):
            direction = forward if signs[i] > 0 else forward[::-1]
            if signs[i] == 0:
                direction = (0, 0)
            self.gpio.output(pin1, direction[0])
            self.gpio.output(pin2, direction[1])
        for pwm, value in zip(self.pwm, values):
            pwm.ChangeDutyCycle(abs(value) * 100)
        self.value = values
        self.last_sign = [new or old for old, new in zip(self.last_sign, signs)]

    def close(self):
        if self.closed:
            return
        self.closed = True
        # Attempt each shutdown operation even if another one fails.
        errors = []
        for pwm in self.pwm:
            try:
                pwm.stop()
            except Exception as exc:
                errors.append(exc)
        for pin in self.pins:
            try:
                self.gpio.output(pin, self.gpio.LOW)
            except Exception as exc:
                errors.append(exc)
        self.value = (0.0, 0.0)
        # Leave the motor enables driven LOW on ordinary exit, rather than
        # floating inputs. A process crash/power loss still needs a hardware stop.
        if errors:
            raise RuntimeError("GPIO shutdown failed; switch off robot power") from errors[0]


class Controller:
    """Single operator; each command needs a fresh, one-use server challenge."""

    def __init__(self, motors, clock=time.monotonic, arm=None):
        self.motors = motors
        self.arm = arm
        self.clock = clock
        self.lock = threading.Lock()
        self.session = None
        self.challenge = None
        self.deadline = 0.0
        self.faulted = False
        self.motion = "stop"

    def _write(self, values):
        try:
            self.motors.set(*values)
        except Exception:
            self.faulted = True
            self.session = self.challenge = None
            self._close_outputs()
            raise

    def _close_outputs(self):
        try:
            self.motors.close()
        finally:
            if self.arm is not None:
                self.arm.close()

    def _stop(self):
        self.session = self.challenge = None
        self.motion = "stop"
        try:
            self._write((0, 0))
        finally:
            if self.arm is not None:
                self.arm.release()

    def _expire(self):
        if self.session is not None and self.clock() >= self.deadline:
            self._stop()

    def _reply(self):
        self.challenge = secrets.token_urlsafe(24)
        self.deadline = self.clock() + TIMEOUT
        result = {"session": self.session, "challenge": self.challenge,
                  "motion": self.motion, "left": self.motors.value[0],
                  "right": self.motors.value[1]}
        if self.arm is not None:
            result["arm"] = self.arm.status()
        return result

    def connect(self):
        with self.lock:
            self._expire()
            if self.faulted:
                raise ControlError("Driver fault: switch off power and restart the app")
            if self.session is not None:
                raise ControlError("Another control page is connected")
            self._stop()
            self.session = secrets.token_urlsafe(24)
            return self._reply()

    def command(self, data):
        with self.lock:
            self._expire()
            if not self.session or data.get("session") != self.session:
                raise ControlError("Session expired; release keys and reconnect")
            if data.get("challenge") != self.challenge:
                self._stop()
                raise ControlError("Stale command rejected; reconnect")
            motion = data.get("motion")
            deadman = data.get("deadman")
            speed = data.get("speed", DEFAULT_SPEED)
            if not isinstance(motion, str) or motion not in MOTIONS or type(deadman) is not bool:
                self._stop()
                raise ControlError("Invalid control command")
            # The range check also rejects NaN and infinities without coercing input.
            if type(speed) not in (int, float) or not 0 <= speed <= MAX_SPEED:
                self._stop()
                raise ControlError("Speed must be a number between 0 and 1 (0–100% duty)")
            if self.arm is not None:
                try:
                    self.arm.configure(data.get("arm", {"enabled": False}))
                except ValueError as exc:
                    self._stop()
                    raise ControlError(str(exc)) from None
                except Exception:
                    self.faulted = True
                    self.session = self.challenge = None
                    self._close_outputs()
                    raise
            self.motion = motion if deadman else "stop"
            if speed == 0:
                self.motion = "stop"
            self._write(tuple(v * speed for v in MOTIONS[self.motion]))
            return self._reply()

    def disconnect(self, session):
        with self.lock:
            if self.session is not None and session == self.session:
                self._stop()

    def watchdog(self):
        with self.lock:
            self._expire()
            if self.arm is not None and self.session is not None and not self.faulted:
                try:
                    self.arm.step()
                except Exception:
                    self.faulted = True
                    self.session = self.challenge = None
                    self._close_outputs()
                    raise

    def close(self):
        with self.lock:
            self.session = self.challenge = None
            self.faulted = True
            self.motion = "stop"
            self._close_outputs()
