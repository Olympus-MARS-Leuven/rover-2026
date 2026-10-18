import http.client
import json
import re
import threading
import unittest

from drive import Controller, SimulatedMotors
from robotino_app import LocalServer, make_handler


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.motors = SimulatedMotors()
        self.control = Controller(self.motors)
        self.server = LocalServer(("127.0.0.1", 0), make_handler(self.control))
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01})
        self.thread.start()
        _, html = self.request("GET", "/")
        self.token = re.search(r'name="robotino-token" content="([^"]+)"', html).group(1)

    def tearDown(self):
        self.server.shutdown()
        self.control.close()
        self.server.server_close()
        self.thread.join()

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

    def test_page_and_asset_are_available(self):
        status, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("SIMULATION", body)
        self.assertNotIn("__TOKEN__", body)
        self.assertIn('max="100" step="5" value="50"', body)
        self.assertIn("about 2 seconds", body)
        self.assertNotIn("__DEFAULT_SPEED__", body)
        self.assertNotIn("__MAX_SPEED__", body)
        self.assertNotIn("__TIMEOUT__", body)
        self.assertEqual(self.request("GET", "/controls.js")[0], 200)
        self.assertEqual(self.request("GET", "/../drive.py")[0], 404)

    def test_missing_token_foreign_origin_and_foreign_host_are_rejected(self):
        self.assertEqual(self.request("POST", "/api/connect", {})[0], 403)
        self.assertEqual(self.request("POST", "/api/connect", {}, {
            "X-Robotino-Token": self.token, "Origin": "https://other.example"})[0], 403)
        self.assertEqual(self.request("GET", "/", headers={"Host": "other.example:8765"})[0], 403)

    def test_connect_drive_and_stop(self):
        status, credentials = self.post("/api/connect", {})
        self.assertEqual(status, 200)
        status, result = self.post("/api/drive", {**credentials, "motion": "forward", "deadman": True})
        self.assertEqual(status, 200)
        self.assertEqual((result["left"], result["right"]), (0.5, 0.5))
        self.assertEqual(self.post("/api/stop", {"session": credentials["session"]})[0], 200)
        self.assertEqual(self.motors.value, (0, 0))
        self.assertEqual(self.post("/api/drive", {**result, "motion": "forward", "deadman": True})[0], 409)

    def test_speed_updates_and_zero_duty_through_http(self):
        _, credentials = self.post("/api/connect", {})
        for speed in (0.75, 1, 0):
            status, credentials = self.post("/api/drive", {
                **credentials, "motion": "forward", "deadman": True, "speed": speed})
            self.assertEqual(status, 200)
            self.assertEqual((credentials["left"], credentials["right"]), (speed, speed))
            self.assertEqual(credentials["motion"], "stop" if speed == 0 else "forward")

    def test_invalid_speed_stops_and_expires_session_through_http(self):
        _, credentials = self.post("/api/connect", {})
        _, credentials = self.post("/api/drive", {
            **credentials, "motion": "forward", "deadman": True, "speed": 0.75})
        status, result = self.post("/api/drive", {
            **credentials, "motion": "forward", "deadman": True, "speed": 75})
        self.assertEqual(status, 409)
        self.assertIn("Speed", result["error"])
        self.assertEqual(self.motors.value, (0, 0))
        self.assertIsNone(self.control.session)


if __name__ == "__main__":
    unittest.main()
