"""Servo limits, motion rates, joint isolation and unified stopping."""

import types
import unittest
from unittest.mock import patch

from arm import Arm, HardwareServos, JOINTS, SimulatedServos
from drive import Controller, ControlError, SimulatedMotors, TIMEOUT
from test_drive import Clock
from test_servo_probe import FakeBus


class ArmTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.driver = SimulatedServos()
        self.arm = Arm(self.driver, self.clock)

    def command(self, **values):
        self.arm.configure({"enabled": True, **values})

    def advance(self, seconds=0.02, count=1):
        for _ in range(count):
            self.clock.now += seconds
            self.arm.step()

    def test_enable_does_not_centre_or_activate_any_joint(self):
        self.command()
        self.advance(count=10)
        self.assertEqual(self.driver.outputs, {})
        self.assertTrue(self.arm.enabled)

    def test_every_slider_reaches_both_configured_limits_and_only_its_joint(self):
        for key, joint in JOINTS.items():
            with self.subTest(key=key):
                self.arm.release()
                for percent, endpoint in ((0, joint.minimum), (100, joint.maximum)):
                    self.command(targets={key: percent}, speed=200)
                    self.advance(0.1, 160)
                    self.assertEqual(self.arm.positions[key], endpoint)
                    self.assertEqual(self.driver.outputs, {joint.channel: endpoint})
                self.arm.release()

    def test_gripper_never_exceeds_observed_closed_position(self):
        self.command(targets={"gripper": 100})
        self.advance(0.1, 10)
        self.assertEqual(self.driver.outputs[15], 330)

    def test_speed_is_adjustable_and_long_scheduling_gap_cannot_jump_to_target(self):
        self.command(targets={"wrist": 100}, speed=100)
        self.advance(0.1)
        self.assertAlmostEqual(self.arm.positions["wrist"], 310)
        self.command(speed=200)
        self.advance(0.1)
        self.assertAlmostEqual(self.arm.positions["wrist"], 330)
        self.advance(10)
        self.assertAlmostEqual(self.arm.positions["wrist"], 350)

    def test_jog_requires_deadman_and_stops_at_key_release_and_endpoints(self):
        self.command(jog={"camera": -1}, deadman=False)
        self.advance(0.1)
        self.assertEqual(self.driver.outputs, {})
        self.command(jog={"camera": -1}, deadman=True)
        self.advance(0.1)
        position = self.arm.positions["camera"]
        self.command(jog={}, deadman=False)
        self.advance(0.1, 5)
        self.assertEqual(self.arm.positions["camera"], position)
        self.command(jog={"camera": -1}, deadman=True)
        self.advance(0.1, 50)
        self.assertEqual(self.arm.positions["camera"], 201)

    def test_hold_cancels_slider_travel_without_releasing_torque(self):
        self.command(targets={"lower": 100})
        self.advance(0.1)
        self.command(hold=True)
        position = self.arm.positions["lower"]
        self.advance(0.1, 10)
        self.assertEqual(self.arm.positions["lower"], position)
        self.assertIn(12, self.driver.outputs)

    def test_release_cancels_old_goals_and_reenable_does_not_restart_motion(self):
        self.command(targets={"wrist": 100})
        self.advance(0.1)
        position = self.arm.positions["wrist"]
        self.arm.release()
        self.command()
        self.advance(0.1, 10)
        self.assertEqual(self.driver.outputs, {})
        self.assertEqual(self.arm.positions["wrist"], position)

    def test_bad_values_cannot_open_a_joint_or_escape_limits(self):
        invalid = [
            {"targets": {"unknown": 50}}, {"targets": {"camera": -1}},
            {"targets": {"camera": 101}}, {"targets": {"camera": True}},
            {"targets": {"camera": float("nan")}}, {"speed": 0}, {"speed": float("inf")},
            {"enabled": "yes"}, {"jog": {"camera": True}}, {"deadman": "yes"},
            {"jog": {"camera": 1, "lower": -1}}, {"hold": "yes"},
        ]
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.command(**values)
        self.assertEqual(self.driver.outputs, {})


class UnifiedStopTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.servos = SimulatedServos()
        self.arm = Arm(self.servos, self.clock)
        self.motors = SimulatedMotors()
        self.control = Controller(self.motors, self.clock, self.arm)
        self.credentials = self.control.connect()

    def command(self, **extra):
        self.credentials = self.control.command({**self.credentials, "motion": "forward", "deadman": True,
                                                "arm": {"enabled": True, "targets": {"lower": 100}}, **extra})

    def test_disconnect_stops_tracks_and_releases_arm(self):
        self.command()
        self.assertTrue(self.servos.outputs)
        self.control.disconnect(self.credentials["session"])
        self.assertEqual(self.motors.value, (0, 0))
        self.assertEqual(self.servos.outputs, {})
        self.assertFalse(self.arm.enabled)

    def test_expiry_releases_arm_and_delayed_commands_cannot_restart_it(self):
        self.command()
        self.clock.now += TIMEOUT + 0.01
        self.control.watchdog()
        self.assertEqual(self.servos.outputs, {})
        with self.assertRaises(ControlError):
            self.command()
        self.credentials = self.control.connect()
        self.assertEqual(self.servos.outputs, {})

    def test_invalid_joint_command_also_stops_moving_tracks(self):
        self.command()
        with self.assertRaises(ControlError):
            self.command(arm={"enabled": True, "targets": {"gripper": 101}})
        self.assertEqual(self.motors.value, (0, 0))
        self.assertEqual(self.servos.outputs, {})

    def test_servo_fault_in_watchdog_stops_everything_and_prevents_reconnect(self):
        self.command()
        self.clock.now += 0.1
        with patch.object(self.servos, "set_position", side_effect=OSError("I2C fault")):
            with self.assertRaises(OSError):
                self.control.watchdog()
        self.assertEqual(self.motors.value, (0, 0))
        self.assertEqual(self.servos.outputs, {})
        with self.assertRaises(ControlError):
            self.control.connect()


class ServoDriverTests(unittest.TestCase):
    def test_hardware_startup_is_silent_and_close_is_idempotent(self):
        bus = FakeBus()
        with patch.dict("sys.modules", {"smbus": types.SimpleNamespace(SMBus=lambda _: bus)}):
            driver = HardwareServos()
        self.assertFalse(any(e[0] == "position" for e in bus.events))
        self.assertEqual(bus.active_channels(), [])
        driver.set_position(11, 300)
        self.assertEqual(bus.active_channels(), [11])
        driver.close()
        driver.close()
        self.assertEqual(bus.active_channels(), [])
        self.assertTrue(bus.closed)

    def test_partial_hardware_initialisation_failure_closes_bus_and_outputs(self):
        bus = FakeBus()
        bus.fail_register = 0xFE
        with patch.dict("sys.modules", {"smbus": types.SimpleNamespace(SMBus=lambda _: bus)}):
            with self.assertRaises(OSError):
                HardwareServos()
        self.assertEqual(bus.active_channels(), [])
        self.assertTrue(bus.closed)


if __name__ == "__main__":
    unittest.main()
