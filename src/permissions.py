"""Decide whether a logged-in user may open a feature.

The whole system boils down to one boolean expression:

    access = IsLoggedIn AND RoleAllowed AND SubscriptionOK

    SubscriptionOK = has_subscription
                     OR role == "Admin"
                     OR the feature does not require a subscription

We test those three parts in order. The first one that fails becomes
the denial message, so a student without analytics permission sees
"Instructor/Admin role required" instead of a subscription error.
"""

from auth import UnknownUserError, notify
from data import FEATURES, ROLE_MESSAGES, USERS


class InvalidFeatureError(Exception):
    """Someone asked for a feature key that is not in FEATURES."""

    def __init__(self, feature_key=""):
        self.feature_key = feature_key
        super(InvalidFeatureError, self).__init__(
            "Unknown feature: {0}".format(feature_key)
        )


def evaluate_access(is_logged_in, role, has_subscription, feature_key):
    """Return (granted, reason) without printing or changing any user.

    This is a "pure" function: same inputs always give the same output.
    That makes it the easy piece to unit test.
    """
    feature = FEATURES.get(feature_key)
    if feature is None:
        raise InvalidFeatureError(feature_key)

    # Check 1 — identity. Nobody gets a feature while logged out.
    if not is_logged_in:
        return False, "Login required"

    # Check 2 — role. Example: Student is not on analytics.allowed_roles.
    allowed_roles = feature.get("allowed_roles") or []
    if role not in allowed_roles:
        roles_text = "/".join(allowed_roles) if allowed_roles else "Valid"
        return False, "{0} role required".format(roles_text)

    # Check 3 — subscription.
    # Admin bypasses this. admin_config also skips it because
    # requires_subscription is False for that feature.
    requires_subscription = bool(feature.get("requires_subscription"))
    subscription_ok = (
        bool(has_subscription)
        or role == "Admin"
        or (not requires_subscription)
    )
    if not subscription_ok:
        return False, "Active subscription required"

    return True, "Access granted"


def welcome_user(username):
    """Print the role's welcome line and a one-line dashboard summary."""
    user = USERS.get(username)
    if user is None:
        print("Cannot show welcome: unknown user.")
        return

    role = user.get("role", "")
    has_sub = bool(user.get("has_active_subscription"))
    message = ROLE_MESSAGES.get(role)
    if message:
        print(message)
    else:
        print("Welcome, {0}.".format(role or username))

    # Extra hint for students whose plan has lapsed.
    if role == "Student" and not has_sub:
        print("Reminder: please renew your subscription.")

    print(
        "Evaluating Role Permissions [Role: {0} | Active Sub: {1}] ...".format(
            role, has_sub
        )
    )


def report_feature_access(username, feature_key):
    """Look up the user, run evaluate_access, and print GRANTED or DENIED.

    Granted example:  GRANTED (Read Only)   <- student's grades level
    Denied example:   DENIED (Admin role required)

    A denial also stores a notification: renew the plan, or record that
    they tried a feature their role cannot open.
    """
    try:
        user = USERS.get(username)
        if user is None:
            raise UnknownUserError(username)

        role = user.get("role")
        has_sub = bool(user.get("has_active_subscription"))
        granted, reason = evaluate_access(True, role, has_sub, feature_key)

        feature = FEATURES.get(feature_key, {})
        label = feature.get("label", feature_key)

        if granted:
            levels = feature.get("access_level") or {}
            level = levels.get(role, "Full")
            print(" - Accessing {0}: GRANTED ({1})".format(label, level))
            return True

        print(" - Accessing {0}: DENIED ({1})".format(label, reason))
        if reason == "Active subscription required":
            notify(username, "Please renew your subscription")
        elif reason != "Login required":
            notify(
                username,
                "Unauthorized attempt to open {0} was recorded.".format(label),
            )
        return False

    except InvalidFeatureError:
        print("That feature does not exist.")
        return False
    except UnknownUserError:
        print("That user does not exist.")
        return False
    except KeyError:
        print("Something went wrong while checking access.")
        return False
