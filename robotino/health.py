"""Pi health readings: under-voltage, throttling, temperature and CPU load.

Under-voltage is the Pi firmware's own warning that the supply dipped below
about 4.63 V, the usual sign of weak or sagging batteries. Every reading is
optional: on a PC the files do not exist and the values are None.
"""

import csv
import logging
from pathlib import Path
import subprocess
import time

THROTTLED = Path("/sys/devices/platform/soc/soc:firmware/get_throttled")
TEMPERATURE = Path("/sys/class/thermal/thermal_zone0/temp")
STAT = Path("/proc/stat")
MEMINFO = Path("/proc/meminfo")
# Bit meanings from the Raspberry Pi documentation for `vcgencmd get_throttled`.
FLAGS = {
    "under_voltage_now": 0, "frequency_capped_now": 1, "throttled_now": 2, "soft_temp_limit_now": 3,
    "under_voltage_seen": 16, "frequency_capped_seen": 17, "throttled_seen": 18, "soft_temp_limit_seen": 19,
}


def decode_throttled(value):
    return {name: bool(value >> bit & 1) for name, bit in FLAGS.items()}


def read_throttled(path=THROTTLED, run=subprocess.run):
    try:
        return int(path.read_text().strip(), 16)
    except (OSError, ValueError):
        pass
    try:  # Older kernels: ask the firmware through vcgencmd.
        output = run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=2).stdout
        return int(output.strip().split("=")[1], 16)
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return None


def read_temperature(path=TEMPERATURE):
    try:
        return round(int(path.read_text().strip()) / 1000, 1)
    except (OSError, ValueError):
        return None


def read_cpu_times(path=STAT):
    try:
        fields = [int(v) for v in path.read_text().splitlines()[0].split()[1:]]
        idle = fields[3] + (fields[4] if len(fields) > 4 else 0)
        return sum(fields), idle
    except (OSError, ValueError, IndexError):
        return None


def read_memory_mb(path=MEMINFO):
    try:
        for line in path.read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return round(int(line.split()[1]) / 1024)
    except (OSError, ValueError, IndexError):
        pass
    return None


class Monitor:
    """Sampled from the app's monitor thread every couple of seconds."""

    def __init__(self, log_dir=None, readers=None, clock=time.monotonic):
        self.readers = readers or {"throttled": read_throttled, "temperature": read_temperature,
                                   "cpu": read_cpu_times, "memory": read_memory_mb}
        self.clock = clock
        self.log_dir = Path(log_dir) if log_dir else None
        self.last_cpu = None
        self.last_log = None
        self.max_temperature = None
        self.under_voltage_events = 0
        self.was_under = False
        self.current = {}
        self.sample()

    def sample(self, extra=None):
        throttled = self.readers["throttled"]()
        temperature = self.readers["temperature"]()
        cpu = self.readers["cpu"]()
        cpu_percent = None
        if cpu and self.last_cpu:
            total, idle = cpu[0] - self.last_cpu[0], cpu[1] - self.last_cpu[1]
            if total > 0:
                cpu_percent = round(100 * (1 - idle / total))
        self.last_cpu = cpu
        flags = decode_throttled(throttled) if throttled is not None else None
        under = bool(flags and flags["under_voltage_now"])
        if under and not self.was_under:
            self.under_voltage_events += 1
            logging.warning("UNDER-VOLTAGE: battery supply too low for the Pi (check batteries)")
        self.was_under = under
        if temperature is not None:
            self.max_temperature = max(temperature, self.max_temperature or temperature)
        self.current = {
            "available": throttled is not None or temperature is not None,
            "throttled": None if throttled is None else f"0x{throttled:x}", "flags": flags,
            "temperature": temperature, "max_temperature": self.max_temperature,
            "cpu_percent": cpu_percent, "memory_mb": self.readers["memory"](),
            "under_voltage_events": self.under_voltage_events,
        }
        if extra is not None:  # The app's periodic samples carry the robot's own state.
            self._log(extra)
        return self.current

    def _log(self, extra, every=10.0):
        """A small CSV per day, for battery and endurance analysis."""
        now = self.clock()
        if self.log_dir is None or (self.last_log is not None and now - self.last_log < every):
            return
        self.last_log = now
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            path = self.log_dir / time.strftime("health-%Y-%m-%d.csv")
            new = not path.exists()
            row = {"time": time.strftime("%H:%M:%S"), "throttled": self.current["throttled"],
                   "under_voltage_now": int(bool(self.current["flags"] and self.current["flags"]["under_voltage_now"])),
                   "temperature": self.current["temperature"], "cpu_percent": self.current["cpu_percent"],
                   "memory_mb": self.current["memory_mb"], **extra}
            with path.open("a", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(row))
                if new:
                    writer.writeheader()
                writer.writerow(row)
        except OSError as exc:
            logging.warning("Health log not written: %s", exc)
            self.log_dir = None
