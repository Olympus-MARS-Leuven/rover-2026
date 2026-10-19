#!/usr/bin/env python3
"""Identify one servo channel with one short pulse; simulation unless --hardware."""

import argparse
from contextlib import ExitStack
import json
import signal
import sys
import time

from drive import GPIOMotors
from hardware import hardware_lock


CHANNELS = (0, 1, 2, 3, 11, 12, 13, 14, 15)
TICKS = tuple(range(285, 316, 5))
PULSE_SECONDS = 0.2
ADDRESS = 0x40
# Nominal 25 MHz oscillator / (4096 * (121 + 1)) = about 50 Hz.
PRESCALE = 121


def validate_probe(channel, ticks):
    if type(channel) is not int or channel not in CHANNELS:
        raise ValueError("Choose one candidate channel: 0-3 or 11-15")
    if type(ticks) is not int or ticks not in TICKS:
        raise ValueError("Identification pulses must be 285-315 ticks in steps of 5")


class PCA9685Probe:
    """Small SMBus driver; never sends a position command to every channel.

    Register sequence: NXP PCA9685 datasheet, sections 7.3.1 and 7.3.4-5.
    ALL_LED writes copy to all channel registers; an individual write then
    enables only that channel. Full-OFF takes priority over full-ON.
    """

    def __init__(self, bus, sleep=time.sleep):
        self.bus = bus
        self.sleep = sleep
        self.ready = False

    def all_off(self):
        # Also works before auto-increment is configured or preparation succeeds.
        self.bus.write_byte_data(ADDRESS, 0xFD, 0x10)

    def prepare(self):
        self.ready = False
        self.all_off()  # Stop any PWM retained from a previous program first.
        if self.bus.read_byte_data(ADDRESS, 0x00) & 0x40:
            raise RuntimeError("External PCA9685 clock selected; power-cycle before testing")
        self.bus.write_byte_data(ADDRESS, 0x00, 0x30)  # Sleep, auto-increment.
        self.bus.write_byte_data(ADDRESS, 0x01, 0x04)  # Non-inverted, totem pole.
        # Clear inherited ON counts/full-ON while all outputs remain full-OFF.
        for register, value in ((0xFA, 0), (0xFB, 0), (0xFC, 0), (0xFD, 0x10)):
            self.bus.write_byte_data(ADDRESS, register, value)
        self.bus.write_byte_data(ADDRESS, 0xFE, PRESCALE)
        self.bus.write_byte_data(ADDRESS, 0x00, 0x20)  # Wake internal oscillator.
        self.sleep(0.005)
        self.bus.write_byte_data(ADDRESS, 0x00, 0xA0)  # Restart with auto-increment.
        self.ready = True

    def pulse(self, channel, ticks):
        validate_probe(channel, ticks)
        if not self.ready:
            raise RuntimeError("Prepare the controller before probing")
        try:
            self.set_position(channel, ticks)
            self.sleep(PULSE_SECONDS)
        finally:
            self.all_off()

    def set_position(self, channel, ticks):
        """Write one position. Caller owns timing, plan limits and release."""
        if type(channel) is not int or channel not in CHANNELS:
            raise ValueError("Invalid servo channel")
        # Outer bounds from the backup's RPIservo.py. Test plans narrow these.
        if type(ticks) is not int or not 100 <= ticks <= 520:
            raise ValueError("Servo position exceeds the original driver's range")
        if not self.ready:
            raise RuntimeError("Prepare the controller before moving a servo")
        self.bus.write_i2c_block_data(
            ADDRESS, 0x06 + 4 * channel, [0, 0, ticks & 0xFF, ticks >> 8])


def probe_hardware(channel, ticks):
    validate_probe(channel, ticks)
    # This OS package is needed only for explicit hardware operation.
    from smbus import SMBus

    with hardware_lock(True), ExitStack() as cleanup:
        # Reuse the driving app's lock and driver to hold both track enables LOW.
        motors = GPIOMotors()
        cleanup.callback(motors.close)
        bus = SMBus(1)
        cleanup.callback(bus.close)
        probe = PCA9685Probe(bus)
        # Register cleanup BEFORE preparation, including partial I2C failures.
        cleanup.callback(probe.all_off)
        probe.prepare()
        probe.pulse(channel, ticks)


def read_status(bus, channel):
    """Read settings only; never prepare the controller or change output registers."""
    validate_probe(channel, 300)
    mode1 = bus.read_byte_data(ADDRESS, 0x00)
    mode2 = bus.read_byte_data(ADDRESS, 0x01)
    prescale = bus.read_byte_data(ADDRESS, 0xFE)
    values = [bus.read_byte_data(ADDRESS, 0x06 + 4 * channel + offset) for offset in range(4)]
    return {
        "address": f"0x{ADDRESS:02x}", "channel": channel,
        "mode1": f"0x{mode1:02x}", "mode2": f"0x{mode2:02x}", "prescale": prescale,
        "asleep": bool(mode1 & 0x10), "external_clock": bool(mode1 & 0x40),
        "auto_increment": bool(mode1 & 0x20), "inverted_output": bool(mode2 & 0x10),
        "nominal_hz_if_internal_25mhz": round(25_000_000 / (4096 * (prescale + 1)), 2),
        "on_ticks": values[0] | ((values[1] & 0x0F) << 8),
        "off_ticks": values[2] | ((values[3] & 0x0F) << 8),
        "full_on": bool(values[1] & 0x10), "full_off": bool(values[3] & 0x10),
    }


def inspect_hardware(channel):
    from smbus import SMBus

    with hardware_lock(True), ExitStack() as cleanup:
        bus = SMBus(1)
        cleanup.callback(bus.close)
        return read_status(bus, channel)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", type=int, choices=CHANNELS, required=True)
    parser.add_argument("--ticks", type=int, choices=TICKS, default=300,
                        help="PWM count near the vendor's starting position; default 300")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--hardware", action="store_true", help="Explicitly pulse a real servo")
    modes.add_argument("--inspect", action="store_true",
                       help="Read real controller registers only; no GPIO or position writes")
    args = parser.parse_args(argv)

    if args.inspect:
        print("READ-ONLY INSPECTION: reads I2C registers; sends no movement or stop commands.")
        print("Existing controller outputs are left as found. This is not an emergency stop.")
        try:
            print(json.dumps(inspect_hardware(args.channel), indent=2))
        except (ImportError, OSError, RuntimeError) as exc:
            print(f"Inspection failed: {exc}", file=sys.stderr)
            return 1
        return 0

    if not args.hardware:
        print(f"SIMULATION: channel {args.channel}, {args.ticks} ticks for {PULSE_SECONDS}s, then release.")
        print("No GPIO or I2C accessed. Add --hardware only when ready for real movement.")
        return 0

    print(f"REAL SERVO: channel {args.channel}, {args.ticks} ticks for {PULSE_SECONDS}s.", flush=True)
    print("Support the arm: initial motion may be large, and release removes holding torque.", flush=True)

    def interrupt(*_):
        raise KeyboardInterrupt

    previous = {}
    try:
        # SSH disconnects normally send SIGHUP; Ctrl+C already raises KeyboardInterrupt.
        for name in ("SIGTERM", "SIGHUP"):
            sig = getattr(signal, name, None)
            if sig is not None:
                previous[sig] = signal.signal(sig, interrupt)
        probe_hardware(args.channel, args.ticks)
    except KeyboardInterrupt:
        print("Interrupted; attempted to turn all servo signals off.")
        return 130
    except (ImportError, OSError, RuntimeError) as exc:
        print(f"Probe failed: {exc}. Keep servo power off until resolved.", file=sys.stderr)
        return 1
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    print("All servo signals off. Record what moved before choosing another test.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
