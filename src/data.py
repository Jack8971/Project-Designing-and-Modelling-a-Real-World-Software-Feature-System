"""In-memory data for the Learning Platform Access System.

This file acts like a tiny database. Everything the simulation needs
(users, roles, and features) lives in dictionaries here so auth.py and
permissions.py can import one shared copy instead of inventing their
own lists.
"""

import copy
import hashlib
import json
import os

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


# SEED_USERS is the factory-default data. It never changes while the program
# runs. USERS (defined just below it) is the working copy that the rest of
# the code reads and edits, and that can be saved to data/users.json.
#
# Each username maps to a nested dictionary of account fields:
#   password_hash           - hashed password (never the original text)
#   role                    - Student, Instructor, or Admin
#   has_active_subscription - False means the plan expired
#   locked                  - True after too many failed logins
#   notifications           - messages shown after a session, then cleared
SEED_USERS = {
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

# Working copy used by auth.py and permissions.py. Everyone imports this one
# dictionary, so we only ever change it IN PLACE (clear/update), never by
# re-assigning the name, otherwise other files would keep an old copy.
USERS = copy.deepcopy(SEED_USERS)

# ---------------------------------------------------------------------------
# Persistence: save USERS to a JSON file so locks and notifications survive
# after the program closes.
#
# Saving is OFF by default, so the scripted demo and the unit tests always
# start from the same clean data. main.py --interactive turns it ON.
# ---------------------------------------------------------------------------

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "data", "users.json"
)
_persist = False

# A saved record must have all of these fields or we do not trust the file.
REQUIRED_FIELDS = (
    "password_hash",
    "role",
    "has_active_subscription",
    "locked",
    "notifications",
)


def _is_valid(users):
    """True only if the loaded JSON looks like a proper USERS dictionary."""
    if not isinstance(users, dict) or not users:
        return False
    for record in users.values():
        if not isinstance(record, dict):
            return False
        if any(field not in record for field in REQUIRED_FIELDS):
            return False
        if record["role"] not in ROLES:
            return False
        if not isinstance(record["notifications"], list):
            return False
    return True


def _replace_users(new_users):
    """Swap the contents of USERS without changing which object it is."""
    USERS.clear()
    USERS.update(new_users)


def save_users():
    """Write USERS to the JSON file. Does nothing while persistence is off.

    We write to a temporary file first and then swap it in. If the program
    crashes halfway through writing, users.json is never left half-written.
    Returns True if the file was written.
    """
    if not _persist:
        return False
    try:
        folder = os.path.dirname(DATA_FILE)
        if folder:
            os.makedirs(folder, exist_ok=True)
        temp_path = DATA_FILE + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(USERS, handle, indent=2)
        os.replace(temp_path, DATA_FILE)
        return True
    except OSError as error:
        print("Warning: could not save data ({0}).".format(error))
        return False


def enable_persistence(path=None):
    """Turn saving on and load USERS from the JSON file.

    Returns a short status word so main.py can tell the user what happened:
      "created"   - no file yet, so we started from SEED_USERS and saved it
      "loaded"    - file read successfully
      "recovered" - file was unreadable/invalid; it was renamed to
                    users.json.corrupt and we started from SEED_USERS again
    """
    global DATA_FILE, _persist
    if path is not None:
        DATA_FILE = path
    _persist = True

    if not os.path.exists(DATA_FILE):
        _replace_users(copy.deepcopy(SEED_USERS))
        save_users()
        return "created"

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (OSError, ValueError):
        loaded = None

    if not _is_valid(loaded):
        try:
            os.replace(DATA_FILE, DATA_FILE + ".corrupt")
        except OSError:
            pass
        _replace_users(copy.deepcopy(SEED_USERS))
        save_users()
        return "recovered"

    _replace_users(loaded)
    return "loaded"


def use_seed_data():
    """Go back to the factory data and turn saving OFF (demo and tests)."""
    global _persist
    _persist = False
    _replace_users(copy.deepcopy(SEED_USERS))


def reset_data():
    """Restore the factory data. If saving is on, overwrite the JSON file."""
    _replace_users(copy.deepcopy(SEED_USERS))
    save_users()


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