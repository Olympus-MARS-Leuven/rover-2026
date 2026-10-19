#!/usr/bin/env python3
"""Test one original Robotino servo with a finite ramp; simulation by default."""

import argparse
from contextlib import ExitStack
from dataclasses import dataclass
import signal
import sys
import time

from drive import GPIOMotors
from hardware import hardware_lock
from servo_probe import PCA9685Probe, PRESCALE, read_status


@dataclass(frozen=True)
class Servo:
    name: str
    minimum: int
    maximum: int
    direction: int


# webServer.py command channels, RPIservo.py neutral=300, config.txt bounds
# from robotino-original-2026-10-18.tar.gz. These are reference values, not
# measured mechanical limits. The web server does not load config.txt.
SERVOS = {
    11: Servo("Camera tilt", 201, 300, -1),
    12: Servo("Lower arm joint", 300, 430, 1),
    13: Servo("Upper arm joint", 139, 443, -1),
    14: Servo("Wrist rotation", 300, 500, 1),
    15: Servo("Gripper", 300, 500, 1),
}
NEUTRAL = 300
WINDOW = 40
STEP_SECONDS = 0.04
HOLD_SECONDS = 0.4


def make_plan(channel, travel=30, direction=None):
    """Build and validate the entire movement before opening hardware."""
    if type(channel) is not int or channel not in SERVOS:
        raise ValueError("Choose an original web-app channel, 11-15")
    if type(travel) is not int or travel not in (10, 20, 30, 40):
        raise ValueError("Travel must be 10, 20, 30 or 40 ticks")
    servo = SERVOS[channel]
    direction = servo.direction if direction is None else direction
    if type(direction) is not int or direction not in (-1, 1):
        raise ValueError("Direction must be -1 or 1")
    target = NEUTRAL + direction * travel
    lower = max(NEUTRAL - WINDOW, servo.minimum)
    upper = min(NEUTRAL + WINDOW, servo.maximum)
    if not lower <= target <= upper:
        raise ValueError(f"Channel {channel}: target {target} is outside the test window {lower}-{upper}")
    plan = [(NEUTRAL, HOLD_SECONDS)]
    for start, end, step in ((NEUTRAL, target, direction), (target, NEUTRAL, -direction)):
        plan.extend((ticks, HOLD_SECONDS if ticks == end else STEP_SECONDS)
                    for ticks in range(start + step, end + step, step))
    return tuple(plan)


def run_plan(probe, channel, plan, sleep=time.sleep):
    """Run an approved plan on one channel, checking start and target readback."""
    verified = []
    try:
        probe.prepare()
        for index, (ticks, delay) in enumerate(plan):
            probe.set_position(channel, ticks)
            if index == 0 or delay == HOLD_SECONDS:
                status = read_status(probe.bus, channel)
                if (status["asleep"] or status["external_clock"] or status["inverted_output"]
                        or not status["auto_increment"] or status["prescale"] != PRESCALE
                        or status["full_on"] or status["full_off"]
                        or status["on_ticks"] != 0 or status["off_ticks"] != ticks):
                    raise RuntimeError(f"Position readback mismatch at {ticks} ticks: {status}")
                verified.append(ticks)
            sleep(delay)
    finally:
        probe.all_off()
    return verified


def run_hardware(channel, travel=30, direction=None):
    plan = make_plan(channel, travel, direction)
    from smbus import SMBus

    with hardware_lock(True), ExitStack() as cleanup:
        motors = GPIOMotors()
        cleanup.callback(motors.close)
        bus = SMBus(1)
        cleanup.callback(bus.close)
        probe = PCA9685Probe(bus)
        cleanup.callback(probe.all_off)
        return run_plan(probe, channel, plan)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", type=int, choices=tuple(SERVOS), required=True)
    parser.add_argument("--travel", type=int, choices=(10, 20, 30, 40), default=30,
                        help="Excursion from 300 ticks, default 30")
    parser.add_argument("--direction", choices=("negative", "positive"),
                        help="Override the channel's default direction within its test window")
    parser.add_argument("--hardware", action="store_true", help="Explicitly enable real servo movement")
    args = parser.parse_args(argv)
    direction = None if args.direction is None else (-1 if args.direction == "negative" else 1)
    try:
        plan = make_plan(args.channel, args.travel, direction)
    except ValueError as exc:
        parser.error(str(exc))
    target = plan[args.travel][0]
    mode = "REAL SERVO" if args.hardware else "SIMULATION"
    print(f"{mode}: channel {args.channel} ({SERVOS[args.channel].name})", flush=True)
    print(f"Plan: 300 -> {target} -> 300 ticks, then release; about {sum(d for _, d in plan):.1f}s.", flush=True)
    print("Movement between commanded positions uses 1-tick steps. The initial position is unknown.", flush=True)
    if not args.hardware:
        print("No GPIO or I2C accessed. Add --hardware to run this one-channel test.")
        return 0

    print("Support the arm, clear the gripper, and keep the power switch accessible. Ctrl+C stops.", flush=True)

    def interrupt(*_):
        raise KeyboardInterrupt

    previous = {}
    try:
        for name in ("SIGTERM", "SIGHUP"):
            sig = getattr(signal, name, None)
            if sig is not None:
                previous[sig] = signal.signal(sig, interrupt)
        verified = run_hardware(args.channel, args.travel, direction)
    except KeyboardInterrupt:
        print("Interrupted; attempted to release all servo signals.")
        return 130
    except (ImportError, OSError, RuntimeError) as exc:
        print(f"Servo test failed: {exc}. Switch off servo power before investigating.", file=sys.stderr)
        return 1
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    print("Controller readback verified: " + " -> ".join(map(str, verified)))
    print("Test finished. All servo signals off; track enables LOW.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
