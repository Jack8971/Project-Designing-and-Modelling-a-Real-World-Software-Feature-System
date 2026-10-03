"""Login, password retries, account lockout, and notifications.

Think of this file as the front desk. It decides whether a person is
who they claim to be. It does not decide which classroom they can enter;
that happens in permissions.py after a successful login.
"""

from data import MAX_LOGIN_ATTEMPTS, USERS, hash_password


# ---------------------------------------------------------------------------
# Named errors
# Using our own exception types lets try/except catch a specific problem
# (unknown user vs locked account) instead of a generic crash.
# ---------------------------------------------------------------------------

class UnknownUserError(Exception):
    """The username is not a key in the USERS dictionary."""

    def __init__(self, username=""):
        self.username = username
        super(UnknownUserError, self).__init__(
            "Unknown user: {0}".format(username)
        )


class AccountLockedError(Exception):
    """This account already used up its password attempts."""

    def __init__(self, username=""):
        self.username = username
        super(AccountLockedError, self).__init__(
            "Account locked: {0}".format(username)
        )


# ---------------------------------------------------------------------------
# Notifications (a simple in-memory inbox on each user)
# ---------------------------------------------------------------------------

def notify(username, message):
    """Add one message to the user's notification list.

    Returns False if the username does not exist. We skip unknown users
    instead of crashing, because the demo also tries a fake account
    (ghost_user).
    """
    user = USERS.get(username)
    if user is None:
        return False
    notes = user.get("notifications")
    if notes is None:
        user["notifications"] = [message]
    else:
        notes.append(message)
    return True


def show_notifications(username):
    """Print the inbox, then empty it so old messages are not shown twice."""
    user = USERS.get(username)
    if user is None:
        print("Notifications: (none — unknown user)")
        return

    notes = user.get("notifications") or []
    if not notes:
        print("Notifications: (none)")
    else:
        print("Notifications:")
        for item in notes:
            print("  - {0}".format(item))
        user["notifications"] = []


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def _password_matches(user, password):
    """Hash the typed password and compare it to the stored hash.

    We never compare "alex123" to "alex123" directly. We hash the guess
    and check whether that hash matches password_hash.
    """
    stored = user.get("password_hash")
    if stored is None:
        raise KeyError("password_hash")
    if stored != hash_password(password):
        return False, "Incorrect password"
    return True, "Login successful"


def login(username, password):
    """Check one username and one password.

    Returns a pair: (True/False, short reason). Failures are turned into
    that pair instead of a traceback, so tests and the menu can just
    inspect the boolean.
    """
    try:
        if username is None or str(username).strip() == "":
            return False, "Username is required"

        # .get() returns None instead of raising KeyError on a bad name.
        user = USERS.get(username)
        if user is None:
            raise UnknownUserError(username)
        if user.get("locked"):
            raise AccountLockedError(username)

        return _password_matches(user, password)

    except UnknownUserError:
        return False, "Unknown user"
    except AccountLockedError:
        return False, "Account locked"
    except KeyError:
        return False, "User record is missing data"


def login_with_retries(username, password_attempts, max_attempts=MAX_LOGIN_ATTEMPTS):
    """Try several passwords in a row. Stop on the first correct one.

    Used by the scripted demo, where the password list is already known
    (for example ["wrong", "lee123"]).

    Important rules:
    - Bad username or already-locked account: stop immediately. Extra
      guesses would be wasted, and they would also leak that the name
      exists vs does not exist in different ways if we kept retrying.
    - Wrong password: print "Attempt X/3 failed: ..." and keep going.
    - Three wrong passwords: lock the account and leave a notification.
    """
    try:
        if username is None or str(username).strip() == "":
            return False, "Username is required"

        user = USERS.get(username)
        if user is None:
            raise UnknownUserError(username)
        if user.get("locked"):
            raise AccountLockedError(username)

        attempts_used = 0
        for password in password_attempts or []:
            if attempts_used >= max_attempts:
                break
            attempts_used += 1
            try:
                success, reason = _password_matches(user, password)
            except KeyError:
                return False, "User record is missing data"
            if success:
                return True, "Login successful"
            print(
                "Attempt {0}/{1} failed: {2}".format(
                    attempts_used, max_attempts, reason
                )
            )

        # One or two wrong guesses should not lock the account.
        if attempts_used >= max_attempts:
            user["locked"] = True
            notify(
                username,
                "Your account was locked after too many failed login attempts.",
            )
            return False, "Account locked after too many failed attempts"

        return False, "Login failed"

    except UnknownUserError:
        print("Login failed: unknown username.")
        return False, "Unknown user"
    except AccountLockedError:
        print("Login failed: this account is locked.")
        return False, "Account locked"


def interactive_password_login(username, read_line, max_attempts=MAX_LOGIN_ATTEMPTS):
    """Same retry rules as login_with_retries, but each guess is typed live.

    read_line is normally input(). Passing it in as an argument keeps this
    function easy to test later without typing at a keyboard.
    """
    try:
        user = USERS.get(username)
        if user is None:
            raise UnknownUserError(username)
        if user.get("locked"):
            raise AccountLockedError(username)

        for number in range(1, max_attempts + 1):
            password = read_line("Password: ")
            success, reason = login(username, password)
            if success:
                return True, "Login successful"
            print(
                "Attempt {0}/{1} failed: {2}".format(
                    number, max_attempts, reason
                )
            )

        user["locked"] = True
        notify(
            username,
            "Your account was locked after too many failed login attempts.",
        )
        return False, "Account locked after too many failed attempts"

    except UnknownUserError:
        print("Login failed: unknown username.")
        return False, "Unknown user"
    except AccountLockedError:
        print("Login failed: this account is locked.")
        return False, "Account locked"
    except KeyError:
        return False, "User record is missing data"
