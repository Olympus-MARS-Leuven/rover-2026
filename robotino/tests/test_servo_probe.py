"""Hardware-free checks for the one-channel identification tool."""

from contextlib import contextmanager, nullcontext, redirect_stdout
import io
import unittest
from unittest.mock import patch
import types

import servo_probe
from drive import GPIOMotors
from test_drive import FakeGPIO


class FakeBus:
    """Model PCA9685 ALL_LED copies and auto-increment, including stale PWM."""

    def __init__(self):
        self.registers = {0: 0, 1: 4}
        for channel in range(16):
            for offset, value in enumerate((0, 0, 44, 1)):
                self.registers[6 + 4 * channel + offset] = value
        self.events = []
        self.closed = False
        self.fail_register = None

    def read_byte_data(self, address, register):
        self.events.append(("read", address, register))
        return self.registers.get(register, 0)

    def write_byte_data(self, address, register, value):
        self.events.append(("write", address, register, value))
        if register == self.fail_register:
            raise OSError("I2C write failed")
        if 0xFA <= register <= 0xFD:
            for channel in range(16):
                self.registers[6 + 4 * channel + register - 0xFA] = value
        else:
            self.registers[register] = value

    def write_i2c_block_data(self, address, register, values):
        if not self.registers[0] & 0x20:
            raise AssertionError("Auto-increment must be enabled for channel writes")
        self.events.append(("position", address, register, list(values)))
        for offset, value in enumerate(values):
            self.registers[register + offset] = value

    def active_channels(self):
        return [channel for channel in range(16)
                if not self.registers[9 + 4 * channel] & 0x10]

    def close(self):
        self.closed = True


class ProbeTests(unittest.TestCase):
    def test_status_reports_registers_without_writes_or_gpio_access(self):
        bus = FakeBus()
        bus.registers.update({0: 0xA0, 1: 4, 0xFE: 121, 0x32: 0, 0x33: 0,
                              0x34: 49, 0x35: 0x11})  # Channel 11, 305 ticks, full-OFF.
        initial = bus.registers.copy()
        status = servo_probe.read_status(bus, 11)
        self.assertEqual(bus.registers, initial)
        self.assertTrue(all(e[0] == "read" and e[1] == 0x40 for e in bus.events))
        self.assertEqual(status["off_ticks"], 305)
        self.assertTrue(status["full_off"])
        self.assertFalse(status["full_on"])
        self.assertFalse(status["asleep"])
        self.assertFalse(status["external_clock"])
        self.assertFalse(status["inverted_output"])
        self.assertTrue(status["auto_increment"])
        self.assertEqual(status["nominal_hz_if_internal_25mhz"], 50.03)

    def test_inspection_closes_bus_without_preparing_or_changing_outputs(self):
        bus = FakeBus()  # Intentionally active: inspection must leave it as found.
        initial = bus.registers.copy()
        with patch.dict("sys.modules", {"smbus": types.SimpleNamespace(SMBus=lambda _: bus)}), \
                patch.object(servo_probe, "hardware_lock", lambda _: nullcontext()), \
                patch.object(servo_probe, "GPIOMotors") as motors, \
                patch.object(servo_probe, "PCA9685Probe") as driver:
            servo_probe.inspect_hardware(11)
        motors.assert_not_called()
        driver.assert_not_called()
        self.assertTrue(bus.closed)
        self.assertEqual(bus.registers, initial)

    def test_inspect_cli_selects_read_only_path_and_rejects_hardware_flag(self):
        with patch.object(servo_probe, "inspect_hardware", return_value={}) as inspect, \
                patch.object(servo_probe, "probe_hardware") as pulse, redirect_stdout(io.StringIO()):
            self.assertEqual(servo_probe.main(["--channel", "11", "--inspect"]), 0)
        inspect.assert_called_once_with(11)
        pulse.assert_not_called()
        with redirect_stdout(io.StringIO()), patch("sys.stderr", new=io.StringIO()), self.assertRaises(SystemExit):
            servo_probe.main(["--channel", "11", "--inspect", "--hardware"])

    def test_prepare_turns_inherited_pwm_off_before_changing_frequency(self):
        bus = FakeBus()
        probe = servo_probe.PCA9685Probe(bus, lambda _: None)
        probe.prepare()
        self.assertEqual(bus.events[0], ("write", 0x40, 0xFD, 0x10))
        self.assertEqual(bus.active_channels(), [])
        self.assertEqual(bus.registers[0xFE], 121)
        self.assertEqual(bus.registers[0] & 0x70, 0x20)  # Awake, internal clock, AI.
        self.assertFalse(any(e[0] == "position" for e in bus.events))

    def test_each_candidate_activates_only_the_chosen_channel_then_releases(self):
        for channel in servo_probe.CHANNELS:
            with self.subTest(channel=channel):
                bus = FakeBus()

                def sleep(seconds):
                    if seconds == servo_probe.PULSE_SECONDS:
                        self.assertEqual(bus.active_channels(), [channel])
                        self.assertEqual(bus.registers[8 + 4 * channel], 305 & 0xFF)
                        self.assertEqual(bus.registers[9 + 4 * channel], 305 >> 8)

                probe = servo_probe.PCA9685Probe(bus, sleep)
                probe.prepare()
                probe.pulse(channel, 305)
                self.assertEqual(bus.active_channels(), [])
                self.assertEqual(len([e for e in bus.events if e[0] == "position"]), 1)

    def test_interrupt_or_error_during_pulse_releases_all_channels(self):
        for exception in (KeyboardInterrupt, OSError):
            with self.subTest(exception=exception):
                bus = FakeBus()

                def sleep(seconds):
                    if seconds == servo_probe.PULSE_SECONDS:
                        raise exception()

                probe = servo_probe.PCA9685Probe(bus, sleep)
                probe.prepare()
                with self.assertRaises(exception):
                    probe.pulse(11, 300)
                self.assertEqual(bus.active_channels(), [])

    def test_invalid_channels_and_wide_pulses_are_rejected_without_writes(self):
        bus = FakeBus()
        probe = servo_probe.PCA9685Probe(bus)
        for channel, ticks in ((-1, 300), (16, 300), (4, 300), (True, 300),
                               (11, 100), (11, 500), (11, 301), (11, float("nan"))):
            with self.subTest(channel=channel, ticks=ticks), self.assertRaises(ValueError):
                probe.pulse(channel, ticks)
        self.assertEqual(bus.events, [])

    def test_external_clock_is_rejected_with_all_channels_off(self):
        bus = FakeBus()
        bus.registers[0] = 0x40
        with self.assertRaises(RuntimeError):
            servo_probe.PCA9685Probe(bus).prepare()
        self.assertEqual(bus.active_channels(), [])

    def test_unprepared_driver_cannot_pulse(self):
        bus = FakeBus()
        with self.assertRaises(RuntimeError):
            servo_probe.PCA9685Probe(bus).pulse(11, 300)
        self.assertEqual(bus.events, [])

    def test_default_cli_never_opens_hardware(self):
        with patch.object(servo_probe, "probe_hardware") as hardware, redirect_stdout(io.StringIO()) as out:
            self.assertEqual(servo_probe.main(["--channel", "11"]), 0)
        hardware.assert_not_called()
        self.assertIn("SIMULATION", out.getvalue())

    def test_hardware_cleanup_holds_tracks_off_and_releases_lock_on_errors(self):
        for failure in (None, 0xFE):
            with self.subTest(failure=failure):
                bus = FakeBus()
                bus.fail_register = failure
                gpio = FakeGPIO()
                lock_held = []

                @contextmanager
                def lock(enabled):
                    self.assertTrue(enabled)
                    lock_held.append(True)
                    try:
                        yield
                    finally:
                        lock_held.pop()

                def open_bus(number):
                    self.assertEqual(number, 1)
                    self.assertTrue(lock_held)
                    self.assertEqual((gpio.pins[4], gpio.pins[17]), (0, 0))
                    return bus

                def sleep(_):
                    self.assertTrue(lock_held)

                actual_probe = servo_probe.PCA9685Probe
                with patch.dict("sys.modules", {"smbus": types.SimpleNamespace(SMBus=open_bus)}), \
                        patch.object(servo_probe, "hardware_lock", lock), \
                        patch.object(servo_probe, "GPIOMotors", lambda: GPIOMotors(gpio)), \
                        patch.object(servo_probe, "PCA9685Probe", lambda bus: actual_probe(bus, sleep)):
                    if failure:
                        with self.assertRaises(OSError):
                            servo_probe.probe_hardware(11, 300)
                    else:
                        servo_probe.probe_hardware(11, 300)
                self.assertFalse(lock_held)
                self.assertTrue(bus.closed)
                self.assertEqual(bus.active_channels(), [])
                self.assertEqual((gpio.pins[4], gpio.pins[17]), (0, 0))
                self.assertTrue(all(e[2] == 0 for e in gpio.events if e[0] in ("duty", "start")))


if __name__ == "__main__":
    unittest.main()
