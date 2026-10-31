"""Measured robot settings, stored on the Pi outside the code folder.

The guided setup page writes these values after the user has watched each
joint and track move. A missing or invalid file falls back to the archived
defaults, so the application always starts.
"""

import json
import logging
import math
import os
from pathlib import Path
import time

DEFAULT_DIR = Path.home() / ".config" / "robotino"
# Absolute bounds from the original RPIservo.py; also enforced in servo_probe.py.
GLOBAL_MIN = 100
GLOBAL_MAX = 520
SERVO_CHANNELS = (11, 12, 13, 14, 15)
JOINT_KEYS = ("camera", "lower", "upper", "wrist", "gripper")
LABELS = {
    "camera": ("up", "down"), "lower": ("down", "up"), "upper": ("up", "down"),
    "wrist": ("left", "right"), "gripper": ("open", "close"),
}
MIN_SPAN = 10


def _number(value, low, high):
    return type(value) in (int, float) and math.isfinite(value) and low <= value <= high


def _ticks(value):
    return type(value) is int and GLOBAL_MIN <= value <= GLOBAL_MAX


def validate_joints(joints):
    """Return a cleaned copy or raise ValueError. Every field is optional."""
    if not isinstance(joints, dict) or not set(joints) <= set(JOINT_KEYS):
        raise ValueError("Unknown joint in calibration")
    cleaned = {}
    for key, data in joints.items():
        if not isinstance(data, dict) or not set(data) <= {"channel", "minimum", "maximum", "rest", "positive"}:
            raise ValueError(f"Invalid calibration for {key}")
        item = {}
        if "channel" in data:
            if type(data["channel"]) is not int or data["channel"] not in SERVO_CHANNELS:
                raise ValueError(f"{key}: channel must be one of 11-15")
            item["channel"] = data["channel"]
        for field in ("minimum", "maximum", "rest"):
            if field in data:
                if not _ticks(data[field]):
                    raise ValueError(f"{key}: {field} must be whole ticks within {GLOBAL_MIN}-{GLOBAL_MAX}")
                item[field] = data[field]
        if ("minimum" in item) != ("maximum" in item):
            raise ValueError(f"{key}: save minimum and maximum together")
        if "minimum" in item and item["maximum"] - item["minimum"] < MIN_SPAN:
            raise ValueError(f"{key}: maximum must be at least {MIN_SPAN} ticks above minimum")
        if "positive" in data:
            if data["positive"] not in LABELS[key]:
                raise ValueError(f"{key}: positive direction must be one of {LABELS[key]}")
            item["positive"] = data["positive"]
        cleaned[key] = item
    return cleaned


def validate_tracks(tracks):
    if not isinstance(tracks, dict) or not set(tracks) <= {"min_duty", "trim"}:
        raise ValueError("Invalid track calibration")
    cleaned = {}
    for field, low, high in (("min_duty", 0.0, 0.8), ("trim", 0.5, 1.0)):
        if field in tracks:
            pair = tracks[field]
            if (not isinstance(pair, list) or len(pair) != 2
                    or not all(_number(v, low, high) for v in pair)):
                raise ValueError(f"Track {field} must be [left, right] within {low}-{high}")
            cleaned[field] = [float(v) for v in pair]
    return cleaned


def validate_camera(camera):
    if not isinstance(camera, dict) or not set(camera) <= {"rotation"}:
        raise ValueError("Invalid camera calibration")
    if "rotation" in camera and camera["rotation"] not in (0, 180):
        raise ValueError("Camera rotation must be 0 or 180")
    return dict(camera)


def check_channels(joints):
    """Each servo channel may belong to only one joint after merging."""
    from arm import JOINTS
    channels = [joints.get(key, {}).get("channel", JOINTS[key].channel) for key in JOINT_KEYS]
    if len(set(channels)) != len(channels):
        raise ValueError("Two joints cannot use the same servo channel")


class Store:
    """calibration.json plus the remembered servo positions (arm-state.json)."""

    def __init__(self, directory=DEFAULT_DIR):
        self.directory = Path(directory)
        self.data = {"joints": {}, "tracks": {}, "camera": {}}
        self.remembered = {}
        self.load()

    @property
    def path(self):
        return self.directory / "calibration.json"

    def load(self):
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.data = {"joints": validate_joints(raw.get("joints", {})),
                         "tracks": validate_tracks(raw.get("tracks", {})),
                         "camera": validate_camera(raw.get("camera", {})),
                         "saved_at": raw.get("saved_at")}
            check_channels(self.data["joints"])
        except FileNotFoundError:
            pass
        except (ValueError, AttributeError, TypeError) as exc:
            logging.warning("Ignoring invalid %s (%s); using archived defaults", self.path, exc)
            self.data = {"joints": {}, "tracks": {}, "camera": {}}
        try:
            raw = json.loads((self.directory / "arm-state.json").read_text(encoding="utf-8"))
            self.remembered = {k: v for k, v in raw.items() if k in JOINT_KEYS and _ticks(v)}
        except (FileNotFoundError, ValueError, AttributeError):
            self.remembered = {}

    def _write(self, name, data):
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / name
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)

    def save(self, joints=None, tracks=None, camera=None, check=None):
        """Merge validated sections into the file; returns the new data.

        check(data) may raise to refuse the merged result before anything is written.
        """
        data = {key: dict(value) if isinstance(value, dict) else value for key, value in self.data.items()}
        if joints is not None:
            merged = {k: dict(v) for k, v in data["joints"].items()}
            for key, item in validate_joints(joints).items():
                merged.setdefault(key, {}).update(item)
            check_channels(merged)
            data["joints"] = merged
        if tracks is not None:
            data["tracks"] = {**data["tracks"], **validate_tracks(tracks)}
        if camera is not None:
            data["camera"] = {**data["camera"], **validate_camera(camera)}
        if check is not None:
            check(data)
        data["saved_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._write("calibration.json", data)
        self.data = data
        return data

    def remember(self, positions):
        """Last commanded ticks, so the next start does not jump from 300."""
        self.remembered.update({k: int(v) for k, v in positions.items() if k in JOINT_KEYS and _ticks(int(v))})
        self._write("arm-state.json", self.remembered)

    def report_path(self):
        return self.directory / "reports" / time.strftime("report-%Y%m%d-%H%M%S.md")

    def save_report(self, text):
        path = self.report_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path
