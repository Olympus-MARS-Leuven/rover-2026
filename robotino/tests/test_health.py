"""Under-voltage and temperature readings, with every Pi file faked."""

from pathlib import Path
import tempfile
import unittest

import health
from test_drive import Clock


class HealthTests(unittest.TestCase):
    def test_throttled_bits_are_decoded(self):
        flags = health.decode_throttled(0x50005)
        self.assertTrue(flags["under_voltage_now"] and flags["throttled_now"])
        self.assertTrue(flags["under_voltage_seen"] and flags["throttled_seen"])
        self.assertFalse(flags["frequency_capped_now"] or flags["soft_temp_limit_seen"])

    def test_files_are_read_and_missing_ones_give_none(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "throttled").write_text("50000\n")
            (folder / "temp").write_text("48312\n")
            self.assertEqual(health.read_throttled(folder / "throttled"), 0x50000)
            self.assertEqual(health.read_temperature(folder / "temp"), 48.3)
            self.assertIsNone(health.read_temperature(folder / "missing"))
            no_vcgencmd = lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError())
            self.assertIsNone(health.read_throttled(folder / "missing", run=no_vcgencmd))

    def test_vcgencmd_is_the_fallback(self):
        class Result:
            stdout = "throttled=0x1\n"
        self.assertEqual(health.read_throttled(Path("/nonexistent"), run=lambda *a, **k: Result()), 1)

    def test_monitor_counts_under_voltage_episodes_and_cpu_load(self):
        readings = iter([0, 1, 1, 0, 1])
        cpu = iter([(100, 50), (200, 75), (300, 175), (400, 200), (500, 300)])
        clock = Clock()
        with tempfile.TemporaryDirectory() as directory:
            monitor = health.Monitor(log_dir=directory, clock=clock, readers={
                "throttled": lambda: next(readings), "temperature": lambda: 50.0,
                "cpu": lambda: next(cpu), "memory": lambda: 512})
            for _ in range(4):
                clock.now += 11
                current = monitor.sample({"left": 0.5})
            self.assertEqual(current["under_voltage_events"], 2)
            self.assertEqual(current["cpu_percent"], 0)
            self.assertTrue(current["flags"]["under_voltage_now"])
            logs = list(Path(directory).glob("health-*.csv"))
            self.assertEqual(len(logs), 1)
            lines = logs[0].read_text().splitlines()
            self.assertEqual(lines[0], "time,throttled,under_voltage_now,temperature,cpu_percent,memory_mb,left")
            self.assertEqual(len(lines), 5)

    def test_pc_without_pi_files_reports_unavailable(self):
        monitor = health.Monitor(readers={"throttled": lambda: None, "temperature": lambda: None,
                                          "cpu": lambda: None, "memory": lambda: None})
        self.assertFalse(monitor.current["available"])
        self.assertIsNone(monitor.current["flags"])


if __name__ == "__main__":
    unittest.main()
