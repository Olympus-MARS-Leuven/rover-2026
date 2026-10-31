"""Servo limits, motion rates, joint isolation, start estimates and unified stopping."""

import types
import unittest
from unittest.mock import patch

from arm import ACTIVATION_GAP, Arm, CALIBRATION_SPEED, HOLD_AFTER_STOP, HardwareServos, JOINTS, SimulatedServos
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

    def test_enable_without_known_positions_does_not_centre_or_activate_any_joint(self):
        self.command()
        self.advance(count=10)
        self.assertEqual(self.driver.outputs, {})
        self.assertTrue(self.arm.enabled)

    def test_every_slider_reaches_both_configured_limits_and_moves_only_its_joint(self):
        for key, joint in JOINTS.items():
            with self.subTest(key=key):
                self.arm.release()
                for percent, endpoint in ((0, joint.minimum), (100, joint.maximum)):
                    self.command(targets={key: percent}, speed=200)
                    self.advance(0.1, 160)
                    self.assertEqual(self.arm.positions[key], endpoint)
                    self.assertEqual(self.driver.outputs[joint.channel], endpoint)
                # Joints used earlier are re-powered where they were left, without moving.
                for k, other in JOINTS.items():
                    if k != key and other.channel in self.driver.outputs:
                        self.assertEqual(self.driver.outputs[other.channel], round(self.arm.positions[k]))

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

    def test_stick_jogs_are_proportional_and_several_joints_can_move_together(self):
        self.command(jog={"lower": 0.5, "wrist": -0.25, "upper": 1.0}, deadman=True)
        self.advance(0.1)
        self.assertAlmostEqual(self.arm.positions["lower"], 305)
        self.assertAlmostEqual(self.arm.positions["wrist"], 300)  # Already at its minimum.
        self.assertAlmostEqual(self.arm.positions["upper"], 310)
        self.assertEqual(set(self.driver.outputs), {12, 13, 14})

    def test_hold_cancels_slider_travel_without_releasing_torque(self):
        self.command(targets={"lower": 100})
        self.advance(0.1)
        self.command(hold=True)
        position = self.arm.positions["lower"]
        self.advance(0.1, 10)
        self.assertEqual(self.arm.positions["lower"], position)
        self.assertIn(12, self.driver.outputs)

    def test_release_cancels_old_goals_and_reenable_holds_without_moving(self):
        self.command(targets={"wrist": 100})
        self.advance(0.1)
        position = self.arm.positions["wrist"]
        self.arm.release()
        self.assertEqual(self.driver.outputs, {})
        self.command()
        self.advance(0.1, 10)
        self.assertEqual(self.arm.positions["wrist"], position)
        self.assertEqual(self.driver.outputs, {14: round(position)})

    def test_freeze_keeps_holding_then_releases_after_the_hold_time(self):
        self.command(targets={"lower": 100})
        self.advance(0.1, 3)
        held = dict(self.driver.outputs)
        self.arm.freeze()
        self.advance(0.5, int(HOLD_AFTER_STOP / 0.5) - 1)
        self.assertEqual(self.driver.outputs, held)
        self.assertGreater(self.arm.status()["release_in"], 0)
        self.advance(0.5, 2)
        self.assertEqual(self.driver.outputs, {})
        self.assertIsNone(self.arm.status()["release_in"])

    def test_reenabling_a_frozen_arm_cancels_the_release_and_does_not_jump(self):
        self.command(targets={"lower": 100})
        self.advance(0.1, 3)
        position = self.arm.positions["lower"]
        self.arm.freeze()
        self.advance(1, 3)
        self.command()
        self.advance(1, 20)
        self.assertEqual(self.driver.outputs, {12: round(position)})

    def test_disabled_commands_freeze_and_release_flag_releases_at_once(self):
        self.command(targets={"gripper": 100})
        self.advance(0.1)
        self.arm.configure({"enabled": False})
        self.assertIn(15, self.driver.outputs)
        self.arm.configure({"enabled": False, "release": True})
        self.assertEqual(self.driver.outputs, {})

    def test_bad_values_cannot_open_a_joint_or_escape_limits(self):
        invalid = [
            {"targets": {"unknown": 50}}, {"targets": {"camera": -1}},
            {"targets": {"camera": 101}}, {"targets": {"camera": True}},
            {"targets": {"camera": float("nan")}}, {"speed": 0}, {"speed": float("inf")},
            {"enabled": "yes"}, {"jog": {"camera": True}}, {"jog": {"camera": 1.5}},
            {"jog": {"camera": float("nan")}}, {"deadman": "yes"}, {"hold": "yes"},
            {"release": 1}, {"calibrate": "yes"}, {"ticks": {"lower": 350}},
            {"calibrate": True, "ticks": {"lower": 99}}, {"calibrate": True, "ticks": {"lower": 521}},
            {"calibrate": True, "ticks": {"lower": 300.5}},
        ]
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.command(**values)
        self.assertEqual(self.driver.outputs, {})


class CalibrationModeTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.driver = SimulatedServos()
        self.arm = Arm(self.driver, self.clock)

    def advance(self, seconds, count=1):
        for _ in range(count):
            self.clock.now += seconds
            self.arm.step()

    def test_calibration_jog_passes_archived_limits_slowly_but_never_global_bounds(self):
        self.arm.configure({"enabled": True, "calibrate": True, "speed": 200,
                            "jog": {"lower": -1}, "deadman": True})
        self.advance(0.1)
        self.assertAlmostEqual(self.arm.positions["lower"], 300 - CALIBRATION_SPEED * 0.1)
        self.advance(0.1, 100)
        self.assertEqual(self.arm.positions["lower"], 100)

    def test_ticks_power_an_inactive_joint_at_that_value_then_ramp(self):
        self.arm.configure({"enabled": True, "calibrate": True, "ticks": {"upper": 250}})
        self.assertEqual(self.driver.outputs, {13: 250})
        self.arm.configure({"enabled": True, "calibrate": True, "ticks": {"upper": 260}})
        self.advance(0.1)
        self.assertEqual(self.driver.outputs, {13: 254})

    def test_leaving_calibration_outside_the_limits_does_not_move_the_joint(self):
        self.arm.configure({"enabled": True, "calibrate": True, "ticks": {"lower": 250}})
        self.arm.configure({"enabled": True})
        self.advance(0.1, 20)
        self.assertEqual(self.driver.outputs, {12: 250})
        # Jogging may only bring it back towards its normal range, never jump.
        self.arm.configure({"enabled": True, "jog": {"lower": -1}, "deadman": True})
        self.advance(0.1)
        self.assertEqual(self.arm.positions["lower"], 250)
        self.arm.configure({"enabled": True, "jog": {"lower": 1}, "deadman": True})
        self.advance(0.1)
        self.assertAlmostEqual(self.arm.positions["lower"], 260)


class StartEstimateTests(unittest.TestCase):
    calibration = {"lower": {"rest": 280, "minimum": 270, "maximum": 440},
                   "upper": {"rest": 410}, "wrist": {"positive": "left"}}

    def make(self, remembered=None, on_release=None):
        self.clock = Clock()
        self.driver = SimulatedServos()
        return Arm(self.driver, self.clock, self.calibration, remembered or {}, on_release)

    def test_measured_rest_and_remembered_positions_are_used_as_start(self):
        arm = self.make({"wrist": 420, "lower": 350, "gripper": 315})
        status = arm.status()["joints"]
        self.assertEqual((status["lower"]["ticks"], status["lower"]["start"]), (280, "rest"))
        self.assertEqual((status["wrist"]["ticks"], status["wrist"]["start"]), (420, "remembered"))
        self.assertEqual((status["camera"]["ticks"], status["camera"]["start"]), (300, "unknown"))
        self.assertEqual(status["lower"]["minimum"], 270)
        self.assertEqual(status["wrist"]["labels"], ["right", "left"])

    def test_enable_powers_known_joints_one_at_a_time_where_they_already_are(self):
        arm = self.make({"wrist": 420, "gripper": 315})
        arm.configure({"enabled": True})
        powered = []
        for _ in range(8):
            self.clock.now += ACTIVATION_GAP
            arm.step()
            powered.append(len(self.driver.outputs))
        self.assertEqual(powered[:4], [1, 2, 3, 4])
        self.assertEqual(self.driver.outputs, {12: 280, 13: 410, 14: 420, 15: 315})
        self.assertNotIn(11, self.driver.outputs)  # Camera position unknown: first use only.

    def test_calibration_mode_powers_only_the_joint_under_test(self):
        arm = self.make({"wrist": 420, "gripper": 315})
        arm.configure({"enabled": True, "calibrate": True, "ticks": {"camera": 260}})
        for _ in range(8):
            self.clock.now += ACTIVATION_GAP
            arm.step()
        self.assertEqual(self.driver.outputs, {11: 260})

    def test_release_returns_gravity_joints_to_rest_and_reports_positions(self):
        saved = []
        arm = self.make(on_release=saved.append)
        arm.configure({"enabled": True, "targets": {"lower": 100, "camera": 0}})
        for _ in range(20):
            self.clock.now += 0.1
            arm.step()
        arm.release()
        self.assertEqual(arm.positions["lower"], 280)
        self.assertEqual(arm.status()["joints"]["camera"]["start"], "remembered")
        self.assertEqual(saved[-1]["camera"], 201)

    def test_park_ramps_to_rest_poses(self):
        arm = self.make()
        arm.configure({"enabled": True, "calibrate": True, "ticks": {"lower": 400}})
        arm.configure({"enabled": True, "park": True})
        for _ in range(40):
            self.clock.now += 0.1
            arm.step()
        self.assertEqual(self.driver.outputs[12], 280)
        self.assertEqual(self.driver.outputs[13], 410)

    def test_channel_changes_require_a_released_arm_but_limits_do_not(self):
        arm = self.make()
        arm.configure({"enabled": True, "targets": {"gripper": 50}})
        position = arm.positions["gripper"]
        arm.apply_calibration({"gripper": {"minimum": 290, "maximum": 340}})
        self.assertEqual((arm.limits["gripper"], arm.positions["gripper"]), ((290, 340), position))
        with self.assertRaises(ValueError):
            arm.apply_calibration({"gripper": {"channel": 11}, "camera": {"channel": 15}})
        arm.release()
        arm.apply_calibration({"gripper": {"channel": 11}, "camera": {"channel": 15}})
        self.assertEqual(arm.status()["joints"]["gripper"]["channel"], 11)


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

    def wait(self, seconds):
        for _ in range(int(seconds / 0.5)):
            self.clock.now += 0.5
            self.control.watchdog()

    def test_disconnect_stops_tracks_and_freezes_then_releases_arm(self):
        self.command()
        self.assertTrue(self.servos.outputs)
        self.control.disconnect(self.credentials["session"])
        self.assertEqual(self.motors.value, (0, 0))
        self.assertTrue(self.servos.outputs)
        self.assertFalse(self.arm.enabled)
        self.wait(HOLD_AFTER_STOP + 1)
        self.assertEqual(self.servos.outputs, {})

    def test_expiry_freezes_arm_and_delayed_commands_cannot_restart_it(self):
        self.command()
        self.clock.now += TIMEOUT + 0.01
        self.control.watchdog()
        self.assertGreater(self.control.last_expiry["after"], TIMEOUT)
        self.assertTrue(self.control.last_expiry["moving"])
        held = dict(self.servos.outputs)
        with self.assertRaises(ControlError):
            self.command()
        self.credentials = self.control.connect()
        self.wait(1.5)
        self.assertEqual(self.servos.outputs, held)
        self.wait(HOLD_AFTER_STOP)
        self.assertEqual(self.servos.outputs, {})

    def test_invalid_joint_command_also_stops_moving_tracks(self):
        self.command()
        with self.assertRaises(ControlError):
            self.command(arm={"enabled": True, "targets": {"gripper": 101}})
        self.assertEqual(self.motors.value, (0, 0))
        self.assertFalse(self.arm.enabled)

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
