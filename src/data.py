"""In-memory data for the Learning Platform Access System.

This file acts like a tiny database. Everything the simulation needs
(users, roles, and features) lives in dictionaries here so auth.py and
permissions.py can import one shared copy instead of inventing their
own lists.
"""

import hashlib

# Stop guessing passwords after this many wrong tries.
MAX_LOGIN_ATTEMPTS = 3

# The only roles the access rules know how to handle.
ROLES = ["Student", "Instructor", "Admin"]


def hash_password(password):
    """Turn a password into a SHA-256 hash (a long hex string).

    We store the hash, not the real password. That way the USERS table
    never contains "alex123" in plain text. To check a login, we hash
    what the user typed and compare it to the stored hash.
    """
    text = "" if password is None else str(password)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# Each username maps to a nested dictionary of account fields:
#   password_hash           - hashed password (never the original text)
#   role                    - Student, Instructor, or Admin
#   has_active_subscription - False means the plan expired
#   locked                  - True after too many failed logins
#   notifications           - messages shown after a session, then cleared
USERS = {
    # Happy-path student: logged in + subscribed -> quizzes and grades.
    "student_alex": {
        "password_hash": hash_password("alex123"),
        "role": "Student",
        "has_active_subscription": True,
        "locked": False,
        "notifications": [],
    },
    # Same role as Alex, but the subscription expired.
    "student_sam": {
        "password_hash": hash_password("sam123"),
        "role": "Student",
        "has_active_subscription": False,
        "locked": False,
        "notifications": [],
    },
    # Instructor with an active plan -> analytics is allowed.
    "prof_jordan": {
        "password_hash": hash_password("jordan123"),
        "role": "Instructor",
        "has_active_subscription": True,
        "locked": False,
        "notifications": [],
    },
    # Instructor without a plan. Also used to demo "wrong password, then retry".
    "prof_lee": {
        "password_hash": hash_password("lee123"),
        "role": "Instructor",
        "has_active_subscription": False,
        "locked": False,
        "notifications": [],
    },
    # Admins skip the subscription check even when this flag is False.
    "admin_casey": {
        "password_hash": hash_password("admin123"),
        "role": "Admin",
        "has_active_subscription": False,
        "locked": False,
        "notifications": [],
    },
}

# Keys (quizzes, grades, ...) are what the code looks up.
# label is the friendlier name printed in the terminal.
FEATURES = {
    "quizzes": {
        "label": "Quizzes",
        "allowed_roles": ["Student", "Instructor", "Admin"],
        "requires_subscription": True,
        # What each role can actually do once access is granted.
        "access_level": {
            "Student": "Take Quizzes",
            "Instructor": "Create & Edit",
            "Admin": "Full",
        },
    },
    "grades": {
        "label": "Grades",
        "allowed_roles": ["Student", "Instructor", "Admin"],
        "requires_subscription": True,
        "access_level": {
            "Student": "Read Only",
            "Instructor": "Full Access",
            "Admin": "Full Access",
        },
    },
    # Students are not in allowed_roles, so they are blocked on the role check.
    "analytics": {
        "label": "Analytics",
        "allowed_roles": ["Instructor", "Admin"],
        "requires_subscription": True,
        "access_level": {
            "Instructor": "Course Reports",
            "Admin": "Platform Reports",
        },
    },
    # Admin-only, and it does not require a subscription.
    "admin_config": {
        "label": "Admin Config",
        "allowed_roles": ["Admin"],
        "requires_subscription": False,
        "access_level": {
            "Admin": "Full",
        },
    },
}

# Printed right after a successful login (different sentence per role).
ROLE_MESSAGES = {
    "Student": (
        "Welcome back! You can take quizzes and view your grades."
    ),
    "Instructor": (
        "Welcome, Instructor. You can manage quizzes, grade submissions, "
        "and view course analytics."
    ),
    "Admin": (
        "Administrator access confirmed. You have full platform control."
    ),
}
