"""Checks that users, locks, and notifications survive a restart.

From the repo root:
    python -m unittest discover tests

Every test writes to a temporary folder, never to the real data/users.json.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import data  # noqa: E402
from auth import login_with_retries, notify, show_notifications, unlock_account  # noqa: E402
from data import USERS  # noqa: E402


class TestPersistence(unittest.TestCase):

    def setUp(self):
        self.original_path = data.DATA_FILE
        self.folder = tempfile.mkdtemp()
        self.path = os.path.join(self.folder, "users.json")
        data.use_seed_data()

    def tearDown(self):
        data.use_seed_data()
        data.DATA_FILE = self.original_path
        shutil.rmtree(self.folder, ignore_errors=True)

    def _restart(self):
        """Pretend the program closed and opened again."""
        data.use_seed_data()
        return data.enable_persistence(self.path)

    def test_first_run_creates_file(self):
        self.assertEqual(data.enable_persistence(self.path), "created")
        self.assertTrue(os.path.exists(self.path))

    def test_saving_is_off_by_default(self):
        notify("student_alex", "hello")
        self.assertFalse(os.path.exists(self.path))

    def test_notification_survives_restart(self):
        data.enable_persistence(self.path)
        notify("student_alex", "Please renew your subscription")
        self.assertEqual(self._restart(), "loaded")
        self.assertIn("Please renew your subscription",
                      USERS["student_alex"]["notifications"])

    def test_reading_notifications_clears_them_on_disk(self):
        data.enable_persistence(self.path)
        notify("student_alex", "one-time message")
        show_notifications("student_alex")
        self._restart()
        self.assertEqual(USERS["student_alex"]["notifications"], [])

    def test_lockout_survives_restart(self):
        data.enable_persistence(self.path)
        login_with_retries("student_alex", ["a", "b", "c"])
        self._restart()
        self.assertTrue(USERS["student_alex"]["locked"])
        self.assertTrue(len(USERS["student_alex"]["notifications"]) > 0)

    def test_unlock_survives_restart(self):
        data.enable_persistence(self.path)
        login_with_retries("student_alex", ["a", "b", "c"])
        self.assertTrue(unlock_account("student_alex"))
        self._restart()
        self.assertFalse(USERS["student_alex"]["locked"])

    def test_unlock_unknown_user(self):
        self.assertFalse(unlock_account("ghost_user"))

    def test_corrupt_file_is_recovered(self):
        with open(self.path, "w") as handle:
            handle.write("{ this is not json")
        self.assertEqual(data.enable_persistence(self.path), "recovered")
        self.assertTrue(os.path.exists(self.path + ".corrupt"))
        self.assertIn("student_alex", USERS)

    def test_wrong_shape_is_recovered(self):
        with open(self.path, "w") as handle:
            json.dump({"student_alex": {"role": "Wizard"}}, handle)
        self.assertEqual(data.enable_persistence(self.path), "recovered")

    def test_reset_restores_seed_data(self):
        data.enable_persistence(self.path)
        login_with_retries("student_alex", ["a", "b", "c"])
        data.reset_data()
        self._restart()
        self.assertFalse(USERS["student_alex"]["locked"])
        self.assertEqual(USERS["student_alex"]["notifications"], [])

    def test_users_object_identity_is_kept(self):
        """auth.py and permissions.py import USERS once, so it must never be replaced."""
        before = id(data.USERS)
        data.enable_persistence(self.path)
        self.assertEqual(id(data.USERS), before)


if __name__ == "__main__":
    unittest.main()