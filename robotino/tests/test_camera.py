"""Video stream logic with a fake rpicam-vid process."""

import io
import threading
import unittest

import camera
from test_drive import Clock

FRAME_A = b"\xff\xd8" + b"A" * 50 + b"\xff\xd9"
FRAME_B = b"\xff\xd8" + b"B" * 70 + b"\xff\xd9"


class FakeProcess:
    def __init__(self, data, args):
        self.args = args
        self.stdout = io.BytesIO(data)
        self.stderr = io.BytesIO(b"[0:00:01] INFO Camera camera_manager.cpp\nERROR: no cameras available\n")
        self.terminated = False

    def terminate(self):
        self.terminated = True

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self.terminated = True


class SplitTests(unittest.TestCase):
    def test_frames_split_across_reads_are_reassembled(self):
        data = b"junk" + FRAME_A + FRAME_B
        frames, rest = camera.split_frames(data[:40])
        self.assertEqual(frames, [])
        frames, rest = camera.split_frames(rest + data[40:])
        self.assertEqual(frames, [FRAME_A, FRAME_B])
        self.assertEqual(rest, b"")

    def test_a_trailing_marker_byte_is_kept(self):
        self.assertEqual(camera.split_frames(b"abc\xff"), ([], b"\xff"))


class CameraTests(unittest.TestCase):
    def make(self, data=FRAME_A + FRAME_B):
        self.started = []

        def popen(args, **_):
            process = FakeProcess(data, args)
            self.started.append(process)
            return process

        self.clock = Clock()
        return camera.Camera(program="/usr/bin/rpicam-vid", rotation=180, popen=popen, clock=self.clock)

    def test_command_uses_preset_rotation_and_stdout(self):
        cam = self.make()
        args = cam.command()
        self.assertEqual(args[:2], ["/usr/bin/rpicam-vid", "-t"])
        self.assertIn("--codec", args)
        self.assertEqual(args[args.index("--width") + 1], "640")
        self.assertEqual(args[-2:], ["--rotation", "180"])
        self.assertIn("-o", args)

    def test_a_viewer_starts_the_process_and_receives_frames(self):
        cam = self.make()
        frames = cam.frames()
        received = [next(frames)]
        self.assertEqual(len(self.started), 1)
        self.assertIn(received[0], (FRAME_A, FRAME_B))
        frames.close()
        status = cam.status()
        self.assertEqual(status["viewers"], 0)
        self.assertTrue(status["available"])

    def test_process_exit_reports_an_error_and_ends_viewers(self):
        cam = self.make(data=b"")
        frames = cam.frames()
        self.assertEqual(list(frames), [])
        status = cam.status()
        self.assertFalse(status["running"])
        self.assertIn("Camera stopped", status["error"])

    def test_idle_camera_stops_after_the_last_viewer_leaves(self):
        cam = self.make()
        frames = cam.frames()
        next(frames)
        frames.close()
        cam.running = True
        cam.process = self.started[0]
        self.clock.now += camera.IDLE_STOP + 0.1
        cam.housekeeping()
        self.assertTrue(self.started[0].terminated)
        self.assertFalse(cam.status()["running"])

    def test_settings_are_validated_and_restart_a_running_stream(self):
        cam = self.make()
        with self.assertRaises(ValueError):
            cam.configure(preset="4k")
        with self.assertRaises(ValueError):
            cam.configure(rotation=90)
        cam.running, cam.process = True, FakeProcess(b"", [])
        old = cam.process
        cam.configure(preset="low")
        self.assertTrue(old.terminated)
        self.assertEqual(self.started[-1].args[self.started[-1].args.index("--width") + 1], "424")

    def test_simulated_camera_streams_the_test_card(self):
        cam = camera.Camera(program=None)
        frames = cam.frames()
        frame = next(frames)
        self.assertTrue(frame.startswith(b"\xff\xd8"))
        self.assertTrue(cam.status()["simulated"])
        frames.close()
        cam.close()


if __name__ == "__main__":
    unittest.main()
