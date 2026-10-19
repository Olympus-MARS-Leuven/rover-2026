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
import threading
from urllib.parse import urlsplit

from drive import Controller, ControlError, DEFAULT_SPEED, GPIOMotors, MAX_SPEED, SimulatedMotors, TIMEOUT
from arm import Arm, HardwareServos, SimulatedServos
from hardware import hardware_lock

WEB = Path(__file__).parent / "web"


class LocalServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_handler(controller, hardware=False, servos=False):
    token = secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(TIMEOUT)

        def log_message(self, *_):
            pass  # Avoid 10 access-log messages/second on the Pi.

        def reply(self, code, body, content_type="application/json"):
            if isinstance(body, dict):
                body = json.dumps(body).encode()
            try:
                self.send_response(code)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy",
                                 "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                                 "frame-ancestors 'none'; base-uri 'none'")
                self.end_headers()
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
            if self.path == "/":
                body = (WEB / "index.html").read_text(encoding="utf-8")
                track_mode = "MOTORS ENABLED" if hardware else "TRACK MOTORS DISABLED"
                if not hardware and not servos:
                    track_mode = "SIMULATION — motors disabled"
                body = body.replace("__TOKEN__", token).replace("__MODE__", track_mode)
                body = body.replace("__DEFAULT_SPEED__", str(round(DEFAULT_SPEED * 100))).replace(
                    "__MAX_SPEED__", str(round(MAX_SPEED * 100))).replace("__TIMEOUT__", f"{TIMEOUT:g}")
                body = body.replace("__SERVO_MODE__", "REAL SERVOS" if servos else "SERVOS SIMULATED")
                self.reply(200, body.encode(), "text/html; charset=utf-8")
            elif self.path == "/controls.js":
                self.reply(200, (WEB / "controls.js").read_bytes(), "text/javascript; charset=utf-8")
            else:
                self.reply(404, {"error": "Not found"})

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
                if not 0 < length <= 1024:
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

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hardware", action="store_true", help="Explicitly enable real track motors")
    parser.add_argument("--servos", action="store_true", help="Allow real servos; enable arm in the page to move")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    # Claim the port BEFORE touching hardware. The service is never exposed to LAN.
    with LocalServer(("127.0.0.1", args.port), BaseHTTPRequestHandler) as server:
        with hardware_lock(args.hardware or args.servos), ExitStack() as cleanup:
            # Servo-only mode still holds the real track enables LOW.
            real_motors = GPIOMotors() if args.hardware or args.servos else None
            if real_motors is not None:
                cleanup.callback(real_motors.close)
            motors = real_motors if args.hardware else SimulatedMotors()
            servo_driver = HardwareServos() if args.servos else SimulatedServos()
            cleanup.callback(servo_driver.close)
            controller = Controller(motors, arm=Arm(servo_driver))
            server.RequestHandlerClass = make_handler(controller, args.hardware, args.servos)
            finished = threading.Event()

            def watchdog():
                while not finished.wait(0.02):
                    try:
                        controller.watchdog()
                    except Exception:
                        logging.exception("Watchdog/driver fault: SWITCH OFF ROBOT POWER")
                        controller.close()
                        return

            worker = threading.Thread(target=watchdog, daemon=True)
            worker.start()

            def terminate(*_):
                raise KeyboardInterrupt

            for name in ("SIGTERM", "SIGHUP"):
                sig = getattr(signal, name, None)
                if sig is not None:
                    signal.signal(sig, terminate)
            logging.info("%s | default duty %.0f%%, adjustable up to %.0f%% | timeout %g s",
                         ("REAL MOTORS ENABLED" if args.hardware else
                          "REAL SERVOS / TRACKS DISABLED" if args.servos else "SIMULATION: no GPIO access"),
                         DEFAULT_SPEED * 100, MAX_SPEED * 100, TIMEOUT)
            logging.info("Open http://127.0.0.1:%s via SSH port forwarding. Ctrl+C stops the app.", args.port)
            logging.info("%s | arm starts disabled; joints move only when individually commanded",
                         "REAL SERVOS AVAILABLE" if args.servos else "SERVOS SIMULATED")
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
