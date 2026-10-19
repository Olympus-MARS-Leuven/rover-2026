"""Checks for finite servo motion based on the original web-app mapping."""

from contextlib import contextmanager, redirect_stdout
import io
import types
import unittest
from unittest.mock import patch

from drive import GPIOMotors
from servo_probe import PCA9685Probe
import servo_test
from test_drive import FakeGPIO
from test_servo_probe import FakeBus


class MotionTests(unittest.TestCase):
    def test_default_plans_use_original_channels_and_return_to_neutral_in_small_steps(self):
        for channel, target in ((11, 270), (12, 330), (13, 270), (14, 330), (15, 330)):
            with self.subTest(channel=channel):
                plan = servo_test.make_plan(channel)
                positions = [ticks for ticks, _ in plan]
                self.assertEqual((positions[0], positions[30], positions[-1]), (300, target, 300))
                self.assertEqual(len(positions), 61)
                self.assertTrue(all(abs(b - a) == 1 for a, b in zip(positions, positions[1:])))
                profile = servo_test.SERVOS[channel]
                self.assertTrue(all(profile.minimum <= p <= profile.maximum for p in positions))
                self.assertLess(sum(delay for _, delay in plan), 5)

    def test_invalid_plans_are_rejected_before_opening_hardware(self):
        for args in ((2, 30, None), (True, 30, None), (11, 100, None),
                     (11, 30, 1), (12, 30, -1), (13, 30, True)):
            with self.subTest(args=args), patch.object(servo_test, "hardware_lock") as lock, \
                    patch.object(servo_test, "GPIOMotors") as motors:
                with self.assertRaises(ValueError):
                    servo_test.run_hardware(*args)
                lock.assert_not_called()
                motors.assert_not_called()

    def test_run_activates_only_the_selected_servo_and_checks_all_landmarks(self):
        for channel in servo_test.SERVOS:
            with self.subTest(channel=channel):
                bus = FakeBus()

                def wait(seconds):
                    if seconds != 0.005:  # Oscillator startup has every output OFF.
                        self.assertEqual(bus.active_channels(), [channel])

                probe = PCA9685Probe(bus, lambda _: None)
                plan = servo_test.make_plan(channel)
                verified = servo_test.run_plan(probe, channel, plan, wait)
                self.assertEqual(verified, [300, plan[30][0], 300])
                self.assertEqual(bus.active_channels(), [])
                writes = [e for e in bus.events if e[0] == "position"]
                self.assertEqual(len(writes), len(plan))
                self.assertTrue(all(e[1] == 0x40 and e[2] == 6 + 4 * channel for e in writes))

    def test_readback_failure_releases_signals_and_aborts_before_further_movement(self):
        class WrongReadback(FakeBus):
            def read_byte_data(self, address, register):
                value = super().read_byte_data(address, register)
                return value ^ 1 if register == 8 + 4 * 11 else value

        bus = WrongReadback()
        probe = PCA9685Probe(bus, lambda _: None)
        with self.assertRaisesRegex(RuntimeError, "readback mismatch"):
            servo_test.run_plan(probe, 11, servo_test.make_plan(11), lambda _: None)
        self.assertEqual(bus.active_channels(), [])
        self.assertEqual(len([e for e in bus.events if e[0] == "position"]), 1)

    def test_interrupt_or_i2c_failure_aborts_without_returning_servo_to_neutral(self):
        for error in (KeyboardInterrupt, OSError):
            with self.subTest(error=error):
                bus = FakeBus()
                probe = PCA9685Probe(bus, lambda _: None)
                steps = 0

                def wait(seconds):
                    nonlocal steps
                    if seconds == servo_test.STEP_SECONDS:
                        steps += 1
                        if steps == 2:
                            raise error()

                with self.assertRaises(error):
                    servo_test.run_plan(probe, 11, servo_test.make_plan(11), wait)
                writes = [e for e in bus.events if e[0] == "position"]
                self.assertEqual([e[3][2] | (e[3][3] << 8) for e in writes], [300, 299, 298])
                self.assertEqual(bus.active_channels(), [])

    def test_hardware_setup_and_cleanup_keep_tracks_disabled_even_when_setup_fails(self):
        for failure in (None, 0xFE):
            with self.subTest(failure=failure):
                bus = FakeBus()
                bus.fail_register = failure
                gpio = FakeGPIO()
                held = []

                @contextmanager
                def lock(enabled):
                    self.assertTrue(enabled)
                    held.append(True)
                    try:
                        yield
                    finally:
                        held.pop()

                def open_bus(number):
                    self.assertEqual(number, 1)
                    self.assertTrue(held)
                    self.assertEqual((gpio.pins[4], gpio.pins[17]), (0, 0))
                    return bus

                run = servo_test.run_plan
                with patch.dict("sys.modules", {"smbus": types.SimpleNamespace(SMBus=open_bus)}), \
                        patch.object(servo_test, "hardware_lock", lock), \
                        patch.object(servo_test, "GPIOMotors", lambda: GPIOMotors(gpio)), \
                        patch.object(servo_test, "PCA9685Probe", lambda bus: PCA9685Probe(bus, lambda _: None)), \
                        patch.object(servo_test, "run_plan", lambda p, c, plan: run(p, c, plan, lambda _: None)):
                    if failure:
                        with self.assertRaises(OSError):
                            servo_test.run_hardware(11)
                    else:
                        servo_test.run_hardware(11)
                self.assertFalse(held)
                self.assertTrue(bus.closed)
                self.assertEqual(bus.active_channels(), [])
                self.assertEqual((gpio.pins[4], gpio.pins[17]), (0, 0))
                self.assertTrue(all(e[2] == 0 for e in gpio.events if e[0] in ("duty", "start")))

    def test_cli_defaults_to_simulation_and_shows_actual_plan(self):
        with patch.object(servo_test, "run_hardware") as hardware, redirect_stdout(io.StringIO()) as out:
            self.assertEqual(servo_test.main(["--channel", "11"]), 0)
        hardware.assert_not_called()
        self.assertIn("SIMULATION", out.getvalue())
        self.assertIn("300 -> 270 -> 300", out.getvalue())

    def test_cli_rejects_incompatible_direction_without_hardware_access(self):
        with patch.object(servo_test, "run_hardware") as hardware, \
                patch("sys.stderr", new=io.StringIO()), self.assertRaises(SystemExit):
            servo_test.main(["--channel", "11", "--direction", "positive", "--hardware"])
        hardware.assert_not_called()


if __name__ == "__main__":
    unittest.main()
