"""Automated checks for login and the access-control rule.

From the repo root:
    python -m unittest discover tests

Each test is a small yes/no question ("does a locked account stay
locked?"). If someone changes the rule in permissions.py, these tests
should fail instead of silently shipping the mistake.
"""

import os
import sys
import unittest

# unittest starts from the repo root, but our modules live in src/.
# Adding src/ to sys.path lets us write "import auth" the same way
# python src/main.py does.
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from auth import login, login_with_retries  # noqa: E402
from data import FEATURES, ROLE_MESSAGES, ROLES, USERS  # noqa: E402
from permissions import InvalidFeatureError, evaluate_access  # noqa: E402


class TestSimulation(unittest.TestCase):
    """Login behaviour, lockout, and the three-part access formula."""

    def setUp(self):
        """Start every test with unlocked accounts and empty inboxes.

        Tests share the same USERS dictionary. Without this reset, a
        lockout test would break the next login test.
        """
        for user in USERS.values():
            user["locked"] = False
            user["notifications"] = []

    def test_valid_login(self):
        """The correct password for student_alex should succeed."""
        success, reason = login("student_alex", "alex123")
        self.assertTrue(success)
        self.assertEqual(reason, "Login successful")

    def test_wrong_password(self):
        """A bad password should fail, but not lock on a single try."""
        success, reason = login("student_alex", "not-the-password")
        self.assertFalse(success)
        self.assertEqual(reason, "Incorrect password")

    def test_unknown_user(self):
        """A name that is not in USERS should fail immediately."""
        success, reason = login("ghost_user", "x")
        self.assertFalse(success)
        self.assertEqual(reason, "Unknown user")

    def test_retry_then_success(self):
        """A wrong guess followed by the right password should still log in."""
        success, reason = login_with_retries("prof_lee", ["wrong", "lee123"])
        self.assertTrue(success)
        self.assertEqual(reason, "Login successful")
        self.assertFalse(USERS["prof_lee"]["locked"])

    def test_lockout_after_three_failures(self):
        """Three bad passwords lock the account, even for the real password."""
        success, reason = login_with_retries("student_alex", ["a", "b", "c"])
        self.assertFalse(success)
        self.assertTrue(USERS["student_alex"]["locked"])
        self.assertTrue(len(USERS["student_alex"]["notifications"]) > 0)

        still_ok, locked_reason = login("student_alex", "alex123")
        self.assertFalse(still_ok)
        self.assertEqual(locked_reason, "Account locked")

    def test_not_logged_in_denied_for_everything(self):
        """Logged-out users are blocked before role or subscription is checked."""
        for feature_key in FEATURES:
            granted, reason = evaluate_access(False, "Admin", True, feature_key)
            self.assertFalse(granted)
            self.assertEqual(reason, "Login required")

    def test_student_quiz_with_subscription(self):
        """A subscribed student may take quizzes."""
        granted, reason = evaluate_access(True, "Student", True, "quizzes")
        self.assertTrue(granted)
        self.assertEqual(reason, "Access granted")

    def test_student_quiz_without_subscription(self):
        """An expired student plan is blocked on quizzes."""
        granted, reason = evaluate_access(True, "Student", False, "quizzes")
        self.assertFalse(granted)
        self.assertEqual(reason, "Active subscription required")

    def test_student_cannot_access_analytics(self):
        """Analytics is instructor/admin only, even with a subscription."""
        granted, reason = evaluate_access(True, "Student", True, "analytics")
        self.assertFalse(granted)
        self.assertIn("role required", reason)

    def test_instructor_can_access_analytics_not_admin_config(self):
        """Instructors get analytics, but not the admin configuration page."""
        analytics_ok, _ = evaluate_access(True, "Instructor", True, "analytics")
        self.assertTrue(analytics_ok)

        admin_ok, reason = evaluate_access(
            True, "Instructor", True, "admin_config"
        )
        self.assertFalse(admin_ok)
        self.assertEqual(reason, "Admin role required")

    def test_admin_exempt_from_subscription_and_can_access_admin_config(self):
        """Admins skip the subscription rule and can open admin_config."""
        quizzes_ok, _ = evaluate_access(True, "Admin", False, "quizzes")
        self.assertTrue(quizzes_ok)

        config_ok, reason = evaluate_access(
            True, "Admin", False, "admin_config"
        )
        self.assertTrue(config_ok)
        self.assertEqual(reason, "Access granted")

    def test_invalid_feature_name(self):
        """A made-up feature key should raise InvalidFeatureError."""
        with self.assertRaises(InvalidFeatureError):
            evaluate_access(True, "Admin", True, "not_a_real_feature")

    def test_role_specific_message_exists_for_each_role(self):
        """Every role in ROLES has a welcome sentence in ROLE_MESSAGES."""
        for role in ROLES:
            self.assertIn(role, ROLE_MESSAGES)
            self.assertTrue(ROLE_MESSAGES[role])


if __name__ == "__main__":
    unittest.main()
