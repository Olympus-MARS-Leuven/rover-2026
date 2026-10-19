"""Shared hardware ownership and Pi checks. Importing this never opens GPIO."""

from contextlib import contextmanager
from pathlib import Path


@contextmanager
def hardware_lock(enabled):
    if not enabled:
        yield
        return
    import fcntl
    import os
    if not Path("/proc/device-tree/model").read_text().startswith("Raspberry Pi 3 Model B "):
        raise RuntimeError("This hardware driver is configured only for the Raspberry Pi 3 Model B")
    cmdline = Path("/proc/cmdline").read_text()
    if any(s in cmdline for s in ("console=serial", "console=ttyAMA", "console=ttyS")):
        raise RuntimeError("Disable the serial login console in raspi-config before motor tests")
    if os.geteuid() == 0:
        raise RuntimeError("Run as your normal user, without sudo (use the gpio group)")
    with open(f"/tmp/robotino-drive-{os.getuid()}.lock", "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another Robotino hardware process is already running") from None
        yield
