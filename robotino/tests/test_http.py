import http.client
import json
from pathlib import Path
import re
import tempfile
import threading
import unittest

from drive import Controller, SimulatedMotors
from arm import Arm, SimulatedServos
from calibration import Store
from camera import Camera
from robotino_app import LocalServer, Services, make_handler


class HTTPTests(unittest.TestCase):
    hardware = False
    servos = False

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.store = Store(self.directory.name)
        self.motors = SimulatedMotors()
        self.arm = Arm(SimulatedServos())
        self.control = Controller(self.motors, arm=self.arm)
        self.camera = Camera(program=None)
        self.services = Services(self.store, self.camera, None, "test-version")
        self.server = LocalServer(("127.0.0.1", 0), make_handler(
            self.control, self.hardware, self.servos, self.services))
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01})
        self.thread.start()
        _, html = self.request("GET", "/")
        self.token = re.search(r'name="robotino-token" content="([^"]+)"', html).group(1)

    def tearDown(self):
        self.server.shutdown()
        self.control.close()
        self.camera.close()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def request(self, method, path, data=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        conn.request(method, path, body=json.dumps(data) if data is not None else None, headers=headers or {})
        response = conn.getresponse()
        result = response.status, response.read().decode()
        conn.close()
        return result

    def post(self, path, data):
        status, body = self.request("POST", path, data, {"X-Robotino-Token": self.token})
        return status, json.loads(body)

    def keys(self, reply):
        return {"session": reply["session"], "challenge": reply["challenge"]}


class SimulationHTTPTests(HTTPTests):
    def test_page_and_assets_are_available(self):
        status, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("SIMULATION", body)
        self.assertIn("test-version", body)
        self.assertNotIn("__TOKEN__", body)
        self.assertIn('max="100" step="5" value="50"', body)
        self.assertIn("about 2 seconds", body)
        for placeholder in ("__DEFAULT_SPEED__", "__MAX_SPEED__", "__TIMEOUT__", "__VERSION__"):
            self.assertNotIn(placeholder, body)
        for asset in ("/controls.js", "/gamepad.js", "/setup.js", "/setup_logic.js"):
            self.assertEqual(self.request("GET", asset)[0], 200, asset)
        self.assertEqual(self.request("GET", "/../drive.py")[0], 404)
        self.assertEqual(self.request("GET", "/test-card.jpg")[0], 404)

    def test_servo_only_banner_clearly_indicates_real_hardware(self):
        self.server.RequestHandlerClass = make_handler(self.control, hardware=False, servos=True)
        status, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("TRACK MOTORS DISABLED", body)
        self.assertIn("REAL SERVOS", body)
        self.assertNotIn("SIMULATION", body)

    def test_missing_token_foreign_origin_and_foreign_host_are_rejected(self):
        self.assertEqual(self.request("POST", "/api/connect", {})[0], 403)
        self.assertEqual(self.request("POST", "/api/status", {})[0], 403)
        self.assertEqual(self.request("POST", "/api/connect", {}, {
            "X-Robotino-Token": self.token, "Origin": "https://other.example"})[0], 403)
        self.assertEqual(self.request("GET", "/", headers={"Host": "other.example:8765"})[0], 403)
        self.assertEqual(self.request("GET", "/video.mjpg?token=wrong")[0], 403)

    def test_connect_drive_and_stop(self):
        status, credentials = self.post("/api/connect", {})
        self.assertEqual(status, 200)
        status, result = self.post("/api/drive", {**self.keys(credentials), "motion": "forward", "deadman": True})
        self.assertEqual(status, 200)
        self.assertEqual((result["left"], result["right"]), (0.5, 0.5))
        self.assertEqual(self.post("/api/stop", {"session": credentials["session"]})[0], 200)
        self.assertEqual(self.motors.value, (0, 0))
        self.assertEqual(self.post("/api/drive", {**self.keys(result), "motion": "forward", "deadman": True})[0], 409)

    def test_analog_tracks_through_http(self):
        _, reply = self.post("/api/connect", {})
        status, reply = self.post("/api/drive", {**self.keys(reply), "motion": "analog",
                                                 "tracks": [1, -0.5], "deadman": True, "speed": 0.8})
        self.assertEqual(status, 200)
        self.assertEqual(self.motors.value, (0.8, -0.4))
        status, reply = self.post("/api/drive", {**self.keys(reply), "motion": "analog",
                                                 "tracks": [2, 0], "deadman": True})
        self.assertEqual(status, 409)
        self.assertEqual(self.motors.value, (0, 0))

    def test_speed_updates_and_zero_duty_through_http(self):
        _, reply = self.post("/api/connect", {})
        for speed in (0.75, 1, 0):
            status, reply = self.post("/api/drive", {
                **self.keys(reply), "motion": "forward", "deadman": True, "speed": speed})
            self.assertEqual(status, 200)
            self.assertEqual((reply["left"], reply["right"]), (speed, speed))
            self.assertEqual(reply["motion"], "stop" if speed == 0 else "forward")

    def test_invalid_speed_stops_and_expires_session_through_http(self):
        _, reply = self.post("/api/connect", {})
        _, reply = self.post("/api/drive", {
            **self.keys(reply), "motion": "forward", "deadman": True, "speed": 0.75})
        status, result = self.post("/api/drive", {
            **self.keys(reply), "motion": "forward", "deadman": True, "speed": 75})
        self.assertEqual(status, 409)
        self.assertIn("Speed", result["error"])
        self.assertEqual(self.motors.value, (0, 0))
        self.assertIsNone(self.control.session)

    def test_arm_enable_is_stationary_then_slider_hold_and_stop_freezes(self):
        _, reply = self.post("/api/connect", {})
        status, reply = self.post("/api/drive", {
            **self.keys(reply), "motion": "stop", "deadman": False, "arm": {"enabled": True}})
        self.assertEqual(status, 200)
        self.assertTrue(reply["arm"]["enabled"])
        self.assertEqual(self.arm.driver.outputs, {})
        status, reply = self.post("/api/drive", {
            **self.keys(reply), "motion": "stop", "deadman": False,
            "arm": {"enabled": True, "targets": {"gripper": 100}}})
        self.assertEqual(status, 200)
        self.assertEqual(self.arm.targets["gripper"], 330)
        self.assertEqual(self.arm.active, {"gripper"})
        status, reply = self.post("/api/drive", {
            **self.keys(reply), "motion": "stop", "deadman": False, "arm": {"enabled": True, "hold": True}})
        self.assertEqual(status, 200)
        self.assertEqual(self.arm.targets["gripper"], self.arm.positions["gripper"])
        self.post("/api/stop", {"session": reply["session"]})
        self.assertIn(15, self.arm.driver.outputs)  # Frozen: still holding.
        _, status = self.post("/api/status", {})
        self.assertGreater(status["controller"]["arm"]["release_in"], 0)

    def test_status_reports_version_modes_camera_and_calibration_without_a_session(self):
        status, result = self.post("/api/status", {})
        self.assertEqual(status, 200)
        self.assertEqual(result["version"], "test-version")
        self.assertFalse(result["tracks_real"] or result["servos_real"])
        self.assertEqual(result["can_save"], {"joints": False, "tracks": False, "camera": False})
        self.assertTrue(result["camera"]["simulated"])
        self.assertEqual(result["calibration"]["joints"], {})
        self.assertFalse(result["controller"]["connected"])

    def test_simulation_cannot_save_calibration_and_keeps_no_report(self):
        _, reply = self.post("/api/connect", {})
        session = reply["session"]
        status, result = self.post("/api/calibration", {"session": session, "joints": {"lower": {"rest": 290}}})
        self.assertEqual(status, 409)
        self.assertIn("--servos", result["error"])
        status, result = self.post("/api/report", {"session": session, "text": "# Practice run"})
        self.assertEqual((status, result), (200, {"saved": None}))
        self.assertEqual(self.post("/api/report", {"session": "wrong", "text": "x"})[0], 409)
        self.assertFalse(Path(self.directory.name, "calibration.json").exists())

    def test_video_streams_the_simulated_test_card_with_the_page_token(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        conn.request("GET", f"/video.mjpg?token={self.token}")
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        self.assertIn("multipart/x-mixed-replace", response.getheader("Content-Type"))
        self.assertIn(b"Content-Type: image/jpeg", response.read(300))
        conn.close()

    def test_camera_settings_are_validated(self):
        self.assertEqual(self.post("/api/camera", {"preset": "low"})[1]["preset"], "low")
        self.assertEqual(self.post("/api/camera", {"preset": "huge"})[0], 409)
        self.assertIn("rpicam-vid not found", self.post("/api/camera", {"probe": True})[1]["probe"])


class RealHardwareHTTPTests(HTTPTests):
    """Same server with both real-hardware flags; the drivers are still simulated."""
    hardware = True
    servos = True

    def test_calibration_is_saved_applied_and_reloaded(self):
        _, reply = self.post("/api/connect", {})
        status, result = self.post("/api/calibration", {
            "session": reply["session"],
            "joints": {"lower": {"minimum": 280, "maximum": 450, "rest": 290, "positive": "down"}},
            "tracks": {"min_duty": [0.3, 0.35], "trim": [1.0, 0.95]}})
        self.assertEqual(status, 200, result)
        self.assertEqual(self.arm.limits["lower"], (280, 450))
        self.assertEqual(self.arm.labels["lower"], ("up", "down"))
        self.assertEqual(self.control.trim, [1.0, 0.95])
        self.assertEqual(Store(self.directory.name).data["joints"]["lower"]["rest"], 290)
        _, reply = self.post("/api/drive", {**self.keys(reply), "motion": "forward", "deadman": True, "speed": 1})
        self.assertEqual(self.motors.value, (1.0, 0.95))

    def test_invalid_or_unsafe_calibration_is_refused(self):
        _, reply = self.post("/api/connect", {})
        session = reply["session"]
        for bad in ({"joints": {"lower": {"minimum": 50, "maximum": 450}}},
                    {"joints": {"lower": {"minimum": 300}}},
                    {"joints": {"camera": {"channel": 12}}},
                    {"tracks": {"trim": [1.2, 1]}}):
            with self.subTest(bad=bad):
                self.assertEqual(self.post("/api/calibration", {"session": session, **bad})[0], 409)
        _, reply = self.post("/api/drive", {**self.keys(reply), "motion": "stop", "deadman": False,
                                            "arm": {"enabled": True, "targets": {"gripper": 50}}})
        # Limits and rest poses may change while powered; servo channels may not.
        status, result = self.post("/api/calibration", {"session": session, "joints": {"lower": {"rest": 290}}})
        self.assertEqual(status, 200, result)
        self.assertIn("gripper", self.arm.active)
        status, result = self.post("/api/calibration", {
            "session": session, "joints": {"lower": {"channel": 13}, "upper": {"channel": 12}}})
        self.assertEqual(status, 409)
        self.assertIn("Release the arm", result["error"])
        self.assertNotIn("channel", Store(self.directory.name).data["joints"].get("lower", {}))

    def test_real_test_report_is_kept_on_the_pi(self):
        _, reply = self.post("/api/connect", {})
        status, result = self.post("/api/report", {"session": reply["session"], "text": "# Real run\n"})
        self.assertEqual(status, 200)
        self.assertEqual(Path(result["saved"]).read_text(encoding="utf-8"), "# Real run\n")


del HTTPTests  # Only the concrete variants run.

if __name__ == "__main__":
    unittest.main()
