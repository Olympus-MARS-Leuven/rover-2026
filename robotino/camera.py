"""Optional on-demand MJPEG video for the control page.

The camera runs in a separate rpicam-vid process, so a camera fault cannot
block the control loop. It starts when the first viewer opens the stream and
stops a few seconds after the last viewer leaves. Without rpicam-vid (on a PC)
a static test card is streamed so the page can be tried in simulation.
"""

from collections import deque
import logging
from pathlib import Path
import shutil
import subprocess
import threading
import time

PRESETS = {"low": (424, 240, 10), "normal": (640, 480, 15), "smooth": (640, 480, 25)}
TEST_CARD = Path(__file__).parent / "web" / "test-card.jpg"
SOI, EOI = b"\xff\xd8", b"\xff\xd9"
MAX_BUFFER = 2_000_000
IDLE_STOP = 3.0
FRAME_WAIT = 8.0  # rpicam-vid needs a few seconds for its first frame on a Pi 3.


def split_frames(buffer):
    """Return (complete JPEG frames, unfinished remainder) from concatenated MJPEG."""
    frames = []
    while True:
        start = buffer.find(SOI)
        if start < 0:
            return frames, buffer[-1:] if buffer.endswith(b"\xff") else b""
        end = buffer.find(EOI, start + 2)
        if end < 0:
            return frames, buffer[start:]
        frames.append(bytes(buffer[start:end + 2]))
        buffer = buffer[end + 2:]


class Camera:
    def __init__(self, program="auto", rotation=0, popen=subprocess.Popen, clock=time.monotonic, run=subprocess.run):
        self.program = shutil.which("rpicam-vid") if program == "auto" else program
        self.simulated = self.program is None
        self.rotation = rotation
        self.preset = "normal"
        self.popen, self.clock, self.run = popen, clock, run
        self.lock = threading.Condition()
        self.frame = None
        self.frame_id = 0
        self.viewers = 0
        self.process = None
        self.stop_event = None
        self.running = False
        self.idle_since = None
        self.error = None
        self.messages = deque(maxlen=12)
        self.times = deque(maxlen=90)

    @property
    def available(self):
        """A real camera program exists (the test card does not count)."""
        return not self.simulated

    def command(self):
        width, height, fps = PRESETS[self.preset]
        args = [self.program, "-t", "0", "-n", "--codec", "mjpeg", "--width", str(width),
                "--height", str(height), "--framerate", str(fps), "--flush", "-o", "-"]
        if self.rotation == 180:
            args += ["--rotation", "180"]
        return args

    def _start(self):
        """Caller holds self.lock."""
        self.error = None
        self.running = True
        if self.simulated:
            self.stop_event = threading.Event()
            threading.Thread(target=self._test_card, args=(self.stop_event,), daemon=True).start()
            return
        try:
            process = self.popen(self.command(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        except OSError as exc:
            self.running = False
            self.error = f"Could not start rpicam-vid: {exc}"
            return
        self.process = process
        threading.Thread(target=self._read, args=(process,), daemon=True).start()
        threading.Thread(target=self._messages, args=(process,), daemon=True).start()
        logging.info("Camera started: %s", " ".join(self.command()[1:]))

    def _test_card(self, stop):
        try:
            frame = TEST_CARD.read_bytes()
        except OSError:
            frame = None
        while frame and not stop.wait(0.2):
            self._publish(frame)

    def _read(self, process):
        buffer = b""
        while True:
            chunk = process.stdout.read(65536)
            if not chunk:
                break
            frames, buffer = split_frames(buffer + chunk)
            if len(buffer) > MAX_BUFFER:
                buffer = b""
            for frame in frames:
                self._publish(frame)
        with self.lock:
            if self.process is process:
                self.process = None
                self.running = False
                tail = " | ".join(list(self.messages)[-3:])
                self.error = f"Camera stopped. {tail}" if tail else "Camera stopped"
                logging.warning("%s", self.error)
            self.lock.notify_all()

    def _messages(self, process):
        for line in iter(process.stderr.readline, b""):
            text = line.decode("utf-8", "replace").strip()
            if text:
                self.messages.append(text[:200])

    def _publish(self, frame):
        with self.lock:
            self.frame = frame
            self.frame_id += 1
            self.times.append(self.clock())
            self.lock.notify_all()

    def frames(self):
        """Generator for one viewer; ends when the camera stops or stalls."""
        with self.lock:
            self.viewers += 1
            self.idle_since = None
            if not self.running:
                self._start()
            last = self.frame_id
        try:
            while True:
                with self.lock:
                    self.lock.wait_for(lambda: self.frame_id != last or not self.running, FRAME_WAIT)
                    if self.frame_id == last:
                        return
                    frame, last = self.frame, self.frame_id
                yield frame
        finally:
            with self.lock:
                self.viewers -= 1
                if self.viewers == 0:
                    self.idle_since = self.clock()

    def _stop(self):
        """Caller holds self.lock."""
        self.running = False
        if self.stop_event is not None:
            self.stop_event.set()
            self.stop_event = None
        process, self.process = self.process, None
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        self.lock.notify_all()

    def housekeeping(self):
        with self.lock:
            if (self.running and self.viewers == 0 and self.idle_since is not None
                    and self.clock() - self.idle_since >= IDLE_STOP):
                self._stop()
                logging.info("Camera stopped: no viewers")

    def configure(self, preset=None, rotation=None):
        if preset is not None and preset not in PRESETS:
            raise ValueError("Unknown video preset")
        if rotation is not None and rotation not in (0, 180):
            raise ValueError("Rotation must be 0 or 180")
        with self.lock:
            changed = (preset or self.preset) != self.preset or (rotation if rotation is not None else self.rotation) != self.rotation
            self.preset = preset or self.preset
            self.rotation = self.rotation if rotation is None else rotation
            if changed and self.running and not self.simulated:
                self._stop()
                self._start()  # Viewers keep waiting for the restarted stream.

    def probe(self):
        """Which camera does libcamera see? Read-only; takes a few seconds."""
        if self.simulated:
            return "rpicam-vid not found: camera software missing or not a Raspberry Pi."
        try:
            result = self.run([self.program, "--list-cameras"], capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.SubprocessError) as exc:
            return f"Camera probe failed: {exc}"
        return ((result.stdout or "") + (result.stderr or "")).strip()[-4000:] or "No output"

    def status(self):
        with self.lock:
            now = self.clock()
            recent = [t for t in self.times if now - t <= 2.0]
            width, height, fps = PRESETS[self.preset]
            return {"available": not self.simulated, "simulated": self.simulated, "running": self.running,
                    "viewers": self.viewers, "fps": round(len(recent) / 2.0, 1), "preset": self.preset,
                    "width": width, "height": height, "target_fps": fps, "rotation": self.rotation,
                    "frame_bytes": len(self.frame) if self.frame else 0, "error": self.error}

    def close(self):
        with self.lock:
            self._stop()
