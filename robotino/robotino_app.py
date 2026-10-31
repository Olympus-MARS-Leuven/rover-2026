#!/usr/bin/env python3
"""Simulation by default; --hardware enables tracks, --servos enables real servo controls."""

import argparse
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
from pathlib import Path
import secrets
import signal
import socket
import subprocess
import threading
from urllib.parse import parse_qs, urlsplit

from drive import Controller, ControlError, DEFAULT_SPEED, GPIOMotors, MAX_SPEED, SimulatedMotors, TIMEOUT
from arm import Arm, HardwareServos, SimulatedServos
from calibration import DEFAULT_DIR, Store
from camera import Camera
from hardware import hardware_lock
from health import Monitor

HERE = Path(__file__).parent
WEB = HERE / "web"
STATIC = {
    "/controls.js": ("controls.js", "text/javascript; charset=utf-8"),
    "/gamepad.js": ("gamepad.js", "text/javascript; charset=utf-8"),
    "/setup.js": ("setup.js", "text/javascript; charset=utf-8"),
    "/setup_logic.js": ("setup_logic.js", "text/javascript; charset=utf-8"),
}
BODY_LIMITS = {"/api/calibration": 4096, "/api/report": 65536}
BOUNDARY = "robotinoframe"


def read_version():
    """VERSION is written by deploy.ps1; on the PC fall back to Git."""
    try:
        return (HERE / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        pass
    try:
        result = subprocess.run(["git", "describe", "--always", "--dirty"], cwd=HERE,
                                capture_output=True, text=True, timeout=3)
        return f"dev {result.stdout.strip()}" if result.returncode == 0 else "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


class Services:
    """Everything besides the controller that the page can ask about."""

    def __init__(self, store=None, camera=None, monitor=None, version="unknown"):
        self.store = store
        self.camera = camera
        self.monitor = monitor
        self.version = version


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_handler(controller, hardware=False, servos=False, services=None):
    token = secrets.token_urlsafe(32)
    services = services or Services()

    def status():
        result = {"version": services.version, "tracks_real": hardware, "servos_real": servos,
                  "controller": controller.status(),
                  "can_save": {"joints": servos, "tracks": hardware,
                               "camera": bool(services.camera and services.camera.available)}}
        if services.monitor is not None:
            result["health"] = services.monitor.current
        if services.camera is not None:
            result["camera"] = services.camera.status()
        if services.store is not None:
            result["calibration"] = services.store.data
        return result

    def save_calibration(data):
        store = services.store
        if store is None:
            raise ControlError("Calibration storage is not available")
        joints, tracks, camera = data.get("joints"), data.get("tracks"), data.get("camera")
        if joints is not None and not servos:
            raise ControlError("Joint calibration is saved only with real servos (--servos)")
        if tracks is not None and not hardware:
            raise ControlError("Track calibration is saved only with real tracks (--hardware)")
        if camera is not None and not (services.camera and services.camera.available):
            raise ControlError("Camera settings are saved only with a real camera")

        def apply(arm):
            check = (lambda data: arm.check_calibration(data["joints"])) if arm is not None else None
            try:
                saved = store.save(joints=joints, tracks=tracks, camera=camera, check=check)
            except ValueError as exc:
                raise ControlError(str(exc)) from None
            if joints is not None and arm is not None:
                arm.apply_calibration(saved["joints"])
            if tracks is not None:
                controller.set_track_calibration(saved["tracks"])
            if camera is not None:
                services.camera.configure(rotation=saved["camera"].get("rotation"))
            return saved

        return {"saved": controller.with_session(data.get("session"), apply)}

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(TIMEOUT)

        def log_message(self, *_):
            pass  # Avoid 10 access-log messages/second on the Pi.

        def headers_common(self, code, content_type, length=None):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            if length is not None:
                self.send_header("Content-Length", str(length))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                             "frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()

        def reply(self, code, body, content_type="application/json"):
            if isinstance(body, dict):
                body = json.dumps(body).encode()
            try:
                self.headers_common(code, content_type, len(body))
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                pass  # The independent watchdog still stops an abandoned session.

        def local_host(self):
            host = self.headers.get("Host", "")
            try:
                parsed = urlsplit("http://" + host)
                return (parsed.hostname in {"localhost", "127.0.0.1"}
                        and parsed.username is None and parsed.password is None
                        and parsed.path == "" and parsed.query == "" and parsed.fragment == ""
                        and parsed.port is not None)
            except ValueError:
                return False

        def do_GET(self):
            if not self.local_host():
                self.reply(403, {"error": "Open this app through localhost and the SSH tunnel"})
                return
            url = urlsplit(self.path)
            if self.path == "/":
                body = (WEB / "index.html").read_text(encoding="utf-8")
                track_mode = "MOTORS ENABLED" if hardware else "TRACK MOTORS DISABLED"
                if not hardware and not servos:
                    track_mode = "SIMULATION — motors disabled"
                body = body.replace("__TOKEN__", token).replace("__MODE__", track_mode)
                body = body.replace("__DEFAULT_SPEED__", str(round(DEFAULT_SPEED * 100))).replace(
                    "__MAX_SPEED__", str(round(MAX_SPEED * 100))).replace("__TIMEOUT__", f"{TIMEOUT:g}")
                body = body.replace("__SERVO_MODE__", "REAL SERVOS" if servos else "SERVOS SIMULATED")
                body = body.replace("__VERSION__", services.version)
                self.reply(200, body.encode(), "text/html; charset=utf-8")
            elif self.path in STATIC:
                name, content_type = STATIC[self.path]
                self.reply(200, (WEB / name).read_bytes(), content_type)
            elif url.path == "/video.mjpg":
                self.video(parse_qs(url.query).get("token", [""])[0])
            else:
                self.reply(404, {"error": "Not found"})

        def video(self, supplied):
            if not secrets.compare_digest(supplied, token):
                self.reply(403, {"error": "Request not authorised"})
                return
            if services.camera is None:
                self.reply(503, {"error": "Video is switched off (--no-camera)"})
                return
            try:
                self.headers_common(200, f"multipart/x-mixed-replace; boundary={BOUNDARY}")
                for frame in services.camera.frames():
                    self.wfile.write(f"--{BOUNDARY}\r\nContent-Type: image/jpeg\r\n"
                                     f"Content-Length: {len(frame)}\r\n\r\n".encode())
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
            except (BrokenPipeError, ConnectionResetError, TimeoutError, socket.timeout):
                pass  # The viewer closed the page or stopped the video.

        def do_POST(self):
            origin = self.headers.get("Origin")
            expected_origin = "http://" + self.headers.get("Host", "")
            if (not self.local_host() or origin not in (None, expected_origin)
                    or self.headers.get("X-Robotino-Token") != token):
                self.reply(403, {"error": "Request not authorised"})
                return
            try:
                if self.headers.get("Transfer-Encoding"):
                    raise ValueError("Chunked bodies are not accepted")
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= BODY_LIMITS.get(self.path, 1024):
                    raise ValueError("Invalid request size")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Expected an object")
                if self.path == "/api/connect":
                    result = controller.connect()
                elif self.path == "/api/drive":
                    result = controller.command(data)
                elif self.path == "/api/stop":
                    controller.disconnect(data.get("session"))
                    result = {"motion": "stop"}
                elif self.path == "/api/status":
                    result = status()
                elif self.path == "/api/calibration":
                    result = save_calibration(data)
                elif self.path == "/api/report":
                    result = self.report(data)
                elif self.path == "/api/camera":
                    result = self.camera(data)
                else:
                    self.reply(404, {"error": "Not found"})
                    return
                self.reply(200, result)
            except ControlError as exc:
                self.reply(409, {"error": str(exc)})
            except (ValueError, socket.timeout):
                self.reply(400, {"error": "Invalid request"})
            except Exception:
                logging.exception("Control failed; stopping the driver")
                controller.close()
                self.reply(500, {"error": "Driver fault; switch off power and inspect the terminal"})

        def report(self, data):
            text = data.get("text")
            if not isinstance(text, str):
                raise ValueError("Report text missing")
            # Only real test runs are kept on the Pi; simulation reports are just downloaded.
            if services.store is None or not (hardware or servos):
                controller.with_session(data.get("session"), lambda _: None)
                return {"saved": None}
            path = controller.with_session(data.get("session"), lambda _: services.store.save_report(text))
            return {"saved": str(path)}

        def camera(self, data):
            camera = services.camera
            if camera is None:
                raise ControlError("Video is switched off (--no-camera)")
            if data.get("probe") is True:
                return {"probe": camera.probe()}
            try:
                camera.configure(preset=data.get("preset"))
            except ValueError as exc:
                raise ControlError(str(exc)) from None
            return camera.status()

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hardware", action="store_true", help="Explicitly enable real track motors")
    parser.add_argument("--servos", action="store_true", help="Allow real servos; enable arm in the page to move")
    parser.add_argument("--no-camera", action="store_true", help="Do not offer the video stream")
    parser.add_argument("--data-dir", default=str(DEFAULT_DIR), help="Calibration, reports and health logs")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    real = args.hardware or args.servos
    # Claim the port BEFORE touching hardware. The service is never exposed to LAN.
    with LocalServer(("127.0.0.1", args.port), BaseHTTPRequestHandler) as server:
        with hardware_lock(real), ExitStack() as cleanup:
            store = Store(args.data_dir)
            # Servo-only mode still holds the real track enables LOW.
            real_motors = GPIOMotors() if real else None
            if real_motors is not None:
                cleanup.callback(real_motors.close)
            motors = real_motors if args.hardware else SimulatedMotors()
            servo_driver = HardwareServos() if args.servos else SimulatedServos()
            cleanup.callback(servo_driver.close)
            # Only real servo positions are remembered; simulation must not overwrite them.
            arm = Arm(servo_driver, calibration=store.data["joints"], remembered=store.remembered,
                      on_release=store.remember if args.servos else None)
            controller = Controller(motors, arm=arm, tracks=store.data["tracks"])
            camera = None
            if not args.no_camera:
                camera = Camera(rotation=store.data["camera"].get("rotation", 0))
                cleanup.callback(camera.close)
            monitor = Monitor(log_dir=store.directory / "logs" if real else None)
            services = Services(store, camera, monitor, read_version())
            server.RequestHandlerClass = make_handler(controller, args.hardware, args.servos, services)
            finished = threading.Event()

            def watchdog():
                while not finished.wait(0.02):
                    try:
                        controller.watchdog()
                    except Exception:
                        logging.exception("Watchdog/driver fault: SWITCH OFF ROBOT POWER")
                        controller.close()
                        return

            def monitoring():
                while not finished.wait(2.0):
                    try:
                        state = controller.status()
                        active = sum(j["active"] for j in state["arm"]["joints"].values())
                        fps = camera.status()["fps"] if camera else None
                        monitor.sample({"left": state["left"], "right": state["right"],
                                        "arm_joints_powered": active, "camera_fps": fps})
                        if camera:
                            camera.housekeeping()
                    except Exception:
                        logging.exception("Health monitor error (control continues)")

            worker = threading.Thread(target=watchdog, daemon=True)
            worker.start()
            threading.Thread(target=monitoring, daemon=True).start()

            def terminate(*_):
                raise KeyboardInterrupt

            for name in ("SIGTERM", "SIGHUP"):
                sig = getattr(signal, name, None)
                if sig is not None:
                    signal.signal(sig, terminate)
            logging.info("Robotino %s", services.version)
            logging.info("%s | default duty %.0f%%, adjustable up to %.0f%% | timeout %g s",
                         ("REAL MOTORS ENABLED" if args.hardware else
                          "REAL SERVOS / TRACKS DISABLED" if args.servos else "SIMULATION: no GPIO access"),
                         DEFAULT_SPEED * 100, MAX_SPEED * 100, TIMEOUT)
            logging.info("Open http://127.0.0.1:%s via SSH port forwarding. Ctrl+C stops the app.", args.port)
            logging.info("%s | arm starts released | calibration: %s",
                         "REAL SERVOS AVAILABLE" if args.servos else "SERVOS SIMULATED",
                         store.data.get("saved_at") or "none yet (archived limits)")
            if camera is not None:
                logging.info("Video: %s", "simulated test card (rpicam-vid not found)" if camera.simulated
                             else "rpicam-vid, starts when the page shows video")
            try:
                server.serve_forever(poll_interval=0.1)
            except KeyboardInterrupt:
                pass
            finally:
                finished.set()
                controller.close()
                worker.join(timeout=1)
                logging.info("Stopped.")


if __name__ == "__main__":
    main()
