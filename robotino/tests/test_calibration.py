"""Calibration file validation, merging and recovery from bad files."""

import json
from pathlib import Path
import tempfile
import unittest

from calibration import Store, validate_joints, validate_tracks


class CalibrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def test_missing_files_mean_archived_defaults(self):
        store = Store(self.path / "new")
        self.assertEqual(store.data, {"joints": {}, "tracks": {}, "camera": {}})
        self.assertEqual(store.remembered, {})
        self.assertFalse((self.path / "new").exists())

    def test_sections_merge_and_survive_a_reload(self):
        store = Store(self.path)
        store.save(joints={"lower": {"minimum": 280, "maximum": 440}})
        store.save(joints={"lower": {"rest": 290}, "wrist": {"positive": "left"}},
                   tracks={"min_duty": [0.3, 0.32]}, camera={"rotation": 180})
        store.save(tracks={"trim": [1.0, 0.95]})
        data = Store(self.path).data
        self.assertEqual(data["joints"]["lower"], {"minimum": 280, "maximum": 440, "rest": 290})
        self.assertEqual(data["joints"]["wrist"], {"positive": "left"})
        self.assertEqual(data["tracks"], {"min_duty": [0.3, 0.32], "trim": [1.0, 0.95]})
        self.assertEqual(data["camera"], {"rotation": 180})
        self.assertIn("saved_at", data)
        self.assertFalse(list(self.path.glob("*.tmp")))

    def test_invalid_values_are_rejected_before_writing(self):
        bad_joints = [
            {"elbow": {}}, {"lower": []}, {"lower": {"angle": 3}},
            {"lower": {"minimum": 99, "maximum": 300}}, {"lower": {"minimum": 300, "maximum": 521}},
            {"lower": {"minimum": 300, "maximum": 305}}, {"lower": {"minimum": 300}},
            {"lower": {"rest": 300.5}}, {"lower": {"rest": True}}, {"lower": {"positive": "left"}},
            {"lower": {"channel": 3}}, {"lower": {"channel": "12"}},
        ]
        for joints in bad_joints:
            with self.subTest(joints=joints), self.assertRaises(ValueError):
                validate_joints(joints)
        for tracks in ({"min_duty": [0.9, 0.1]}, {"trim": [0.4, 1]}, {"trim": [1]}, {"gain": [1, 1]},
                       {"trim": [float("nan"), 1]}, {"trim": "1,1"}):
            with self.subTest(tracks=tracks), self.assertRaises(ValueError):
                validate_tracks(tracks)
        store = Store(self.path)
        with self.assertRaises(ValueError):
            store.save(joints={"camera": {"channel": 12}})  # Lower arm already uses 12.
        with self.assertRaises(ValueError):
            store.save(camera={"rotation": 90})
        self.assertFalse((self.path / "calibration.json").exists())

    def test_swapped_channels_are_accepted_together(self):
        store = Store(self.path)
        store.save(joints={"lower": {"channel": 13}, "upper": {"channel": 12}})
        self.assertEqual(Store(self.path).data["joints"]["upper"]["channel"], 12)

    def test_a_corrupt_file_is_ignored_with_defaults(self):
        (self.path / "calibration.json").write_text('{"joints": {"lower": {"minimum": 5}}}')
        (self.path / "arm-state.json").write_text("not json")
        store = Store(self.path)
        self.assertEqual(store.data["joints"], {})
        self.assertEqual(store.remembered, {})

    def test_remembered_positions_keep_only_valid_ticks(self):
        store = Store(self.path)
        store.remember({"wrist": 420, "gripper": 315})
        store.remember({"camera": 250})
        (self.path / "arm-state.json").write_text(json.dumps({"wrist": 420, "elbow": 3, "camera": 900}))
        self.assertEqual(Store(self.path).remembered, {"wrist": 420})

    def test_reports_are_written_to_their_own_folder(self):
        path = Store(self.path).save_report("# Test\n")
        self.assertEqual(path.parent, self.path / "reports")
        self.assertEqual(path.read_text(encoding="utf-8"), "# Test\n")


if __name__ == "__main__":
    unittest.main()
