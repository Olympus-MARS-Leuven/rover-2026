"""Hardware-free checks of the behaviours that can otherwise leave tracks moving."""
import unittest

from drive import Controller, ControlError, DEFAULT_SPEED, GPIOMotors, MAX_SPEED, SimulatedMotors, TIMEOUT


class Clock:
    now = 10.0

    def __call__(self):
        return self.now


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.motors = SimulatedMotors()
        self.control = Controller(self.motors, self.clock)
        self.credentials = self.control.connect()

    def command(self, motion="forward", deadman=True, **extra):
        self.credentials = self.control.command(
            {**self.credentials, "motion": motion, "deadman": deadman, **extra})

    def test_connect_is_stationary_and_deadman_is_required(self):
        self.assertEqual(self.motors.value, (0, 0))
        self.command(deadman=False)
        self.assertEqual(self.motors.value, (0, 0))
        self.command()
        self.assertEqual(self.motors.value, (DEFAULT_SPEED, DEFAULT_SPEED))
        self.command(deadman=False)
        self.assertEqual(self.motors.value, (0, 0))

    def test_watchdog_stops_without_any_more_browser_requests(self):
        self.command()
        self.clock.now += TIMEOUT + 0.01
        self.control.watchdog()
        self.assertEqual(self.motors.value, (0, 0))
        self.assertIsNone(self.control.session)

    def test_one_second_delay_does_not_expire_controls(self):
        self.command()
        self.clock.now += 1.0  # The previous 0.4-second timeout disconnected here.
        self.control.watchdog()
        self.assertEqual(self.motors.value, (DEFAULT_SPEED, DEFAULT_SPEED))
        self.command("backward")
        self.assertEqual(self.motors.value, (-DEFAULT_SPEED, -DEFAULT_SPEED))

    def test_selected_speed_changes_while_connected_in_both_directions(self):
        for motion, signs in (("forward", (1, 1)), ("backward", (-1, -1)),
                              ("left", (-1, 1)), ("right", (1, -1))):
            for speed in (0.25, 0.5, 0.75, 1):
                with self.subTest(motion=motion, speed=speed):
                    self.command(motion, speed=speed)
                    self.assertEqual(self.motors.value, tuple(sign * speed for sign in signs))

    def test_zero_speed_and_released_shift_stop_at_full_selected_speed(self):
        self.command(speed=1)
        self.command(speed=0)
        self.assertEqual(self.motors.value, (0, 0))
        self.assertEqual(self.credentials["motion"], "stop")
        self.command(speed=1)
        self.command(deadman=False, speed=1)
        self.assertEqual(self.motors.value, (0, 0))

    def test_invalid_speed_stops_instead_of_clamping_or_accepting_it(self):
        for speed in (-0.01, 1.01, 10**400, "0.5", None, True, [], float("nan"), float("inf")):
            with self.subTest(speed=speed):
                self.command(speed=0.75)
                with self.assertRaises(ControlError):
                    self.command(speed=speed)
                self.assertEqual(self.motors.value, (0, 0))
                self.assertIsNone(self.control.session)
                self.credentials = self.control.connect()

    def test_delayed_request_cannot_restart_after_timeout(self):
        self.clock.now += TIMEOUT + 0.01
        with self.assertRaises(ControlError):
            self.command()
        self.assertEqual(self.motors.value, (0, 0))

    def test_replayed_challenge_stops_and_requires_new_session(self):
        old = self.credentials.copy()
        self.command()
        with self.assertRaises(ControlError):
            self.control.command({**old, "motion": "forward", "deadman": True})
        self.assertEqual(self.motors.value, (0, 0))
        self.assertIsNone(self.control.session)

    def test_second_operator_cannot_take_over(self):
        self.command()
        with self.assertRaises(ControlError):
            self.control.connect()
        self.assertEqual(self.motors.value, (DEFAULT_SPEED, DEFAULT_SPEED))

    def test_old_stop_cannot_interrupt_a_new_session(self):
        old = self.credentials["session"]
        self.control.disconnect(old)
        self.credentials = self.control.connect()
        self.command()
        self.control.disconnect(old)
        self.assertEqual(self.motors.value, (DEFAULT_SPEED, DEFAULT_SPEED))

    def test_invalid_control_stops_active_motion(self):
        self.command()
        with self.assertRaises(ControlError):
            self.command(motion=["forward"])
        self.assertEqual(self.motors.value, (0, 0))

    def test_turns_have_opposite_track_directions(self):
        self.command("left")
        self.assertEqual(self.motors.value, (-DEFAULT_SPEED, DEFAULT_SPEED))
        self.command("right")
        self.assertEqual(self.motors.value, (DEFAULT_SPEED, -DEFAULT_SPEED))

    def test_driver_fault_closes_hardware_and_prevents_reconnect(self):
        class FailingMotors(SimulatedMotors):
            closed = False

            def set(self, left, right):
                if left or right:
                    raise OSError("GPIO failure")
                super().set(left, right)

            def close(self):
                self.closed = True
                super().close()

        motors = FailingMotors()
        control = Controller(motors, self.clock)
        credentials = control.connect()
        with self.assertRaises(OSError):
            control.command({**credentials, "motion": "forward", "deadman": True})
        self.assertTrue(motors.closed)
        self.assertEqual(motors.value, (0, 0))
        with self.assertRaises(ControlError):
            control.connect()

    def test_shutdown_rejects_pending_commands(self):
        self.command()
        self.control.close()
        with self.assertRaises(ControlError):
            self.command()
        self.assertEqual(self.motors.value, (0, 0))


class FakeGPIO:
    BCM, OUT, LOW = "BCM", "OUT", 0

    def __init__(self):
        self.events = []
        self.pins = {}

    def setmode(self, mode):
        self.events.append(("mode", mode))

    def setup(self, pin, mode, initial):
        self.events.append(("setup", pin, initial))
        self.pins[pin] = initial

    def output(self, pin, value):
        self.events.append(("output", pin, value))
        self.pins[pin] = value

    def PWM(self, pin, frequency):
        events = self.events

        class PWM:
            def start(self, duty):
                events.append(("start", pin, duty))

            def ChangeDutyCycle(self, duty):
                events.append(("duty", pin, duty))

            def stop(self):
                events.append(("end", pin, 0))

        return PWM()


class WiringTests(unittest.TestCase):
    def setUp(self):
        self.gpio = FakeGPIO()
        self.motors = GPIOMotors(self.gpio, lambda t: self.gpio.events.append(("wait", t)))

    def test_both_enables_are_low_before_direction_setup(self):
        self.assertEqual(self.gpio.events[1:3], [("setup", 17, 0), ("setup", 4, 0)])
        self.assertEqual([e for e in self.gpio.events if e[0] == "start"],
                         [("start", 17, 0), ("start", 4, 0)])

    def test_forward_polarity_is_corrected_without_a_startup_power_pulse(self):
        self.motors.set(DEFAULT_SPEED, DEFAULT_SPEED)
        self.assertEqual([self.gpio.pins[p] for p in (27, 18, 14, 15)], [1, 0, 0, 1])
        duties = [e for e in self.gpio.events if e[0] == "duty"]
        self.assertEqual(duties, [("duty", 17, 0), ("duty", 4, 0),
                                  ("duty", 17, 50), ("duty", 4, 50)])

    def test_full_duty_is_available_and_excess_duty_is_rejected(self):
        self.motors.set(1, -1)
        self.assertEqual(self.gpio.events[-2:], [("duty", 17, 100), ("duty", 4, 100)])
        with self.assertRaises(ValueError):
            self.motors.set(1.01, 0)

    def test_corrected_turn_polarities(self):
        self.motors.set(-0.5, 0.5)  # Left pivot.
        self.assertEqual([self.gpio.pins[p] for p in (27, 18, 14, 15)], [0, 1, 0, 1])
        self.motors.set(0.5, -0.5)  # Right pivot.
        self.assertEqual([self.gpio.pins[p] for p in (27, 18, 14, 15)], [1, 0, 1, 0])

    def test_reverse_disables_bridges_before_waiting_and_switching(self):
        self.motors.set(MAX_SPEED, MAX_SPEED)
        self.gpio.events.clear()
        self.motors.set(-MAX_SPEED, -MAX_SPEED)
        self.assertEqual(self.gpio.events[:3], [("duty", 17, 0), ("duty", 4, 0), ("wait", 0.05)])
        self.assertEqual([self.gpio.pins[p] for p in (27, 18, 14, 15)], [0, 1, 1, 0])

    def test_close_leaves_enables_low(self):
        self.motors.set(MAX_SPEED, MAX_SPEED)
        self.motors.close()
        self.assertEqual((self.gpio.pins[4], self.gpio.pins[17]), (0, 0))
        with self.assertRaises(RuntimeError):
            self.motors.set(MAX_SPEED, MAX_SPEED)


if __name__ == "__main__":
    unittest.main()
