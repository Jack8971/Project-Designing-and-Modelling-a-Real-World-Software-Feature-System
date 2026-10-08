"""Start the simulation from the terminal.

    python src/main.py                 -> canned demo (best for screenshots)
    python src/main.py --interactive   -> type a username and use menus
                                          (saved to data/users.json)
    python src/main.py --interactive --reset
                                       -> same, but wipe saved data first

This file is mostly "glue": it calls login from auth.py and access
checks from permissions.py, then prints the results in a readable order.
"""

from __future__ import print_function

import os
import sys

from auth import (
    MAX_LOGIN_ATTEMPTS,
    interactive_password_login,
    login_with_retries,
    show_notifications,
    unlock_account,
)
from data import (
    DATA_FILE,
    FEATURES,
    USERS,
    enable_persistence,
    reset_data,
    use_seed_data,
)
from permissions import evaluate_access, report_feature_access, welcome_user

SEPARATOR = "-" * 60


def _safe_input(prompt):
    """Read one typed line and strip leftover spaces."""
    raw = input(prompt)
    if raw is None:
        return ""
    return str(raw).strip()


def prompt_choice(prompt, valid_choices, max_attempts=MAX_LOGIN_ATTEMPTS):
    """Ask for a menu number. After 3 bad answers, go back a level.

    Returning None is how we say "give up on this menu" without crashing
    when someone types "asdf" instead of 1, 2, or 3.
    """
    for _ in range(max_attempts):
        choice = _safe_input(prompt)
        if choice in valid_choices:
            return choice
        print("Invalid input. Please try again.")
    print("Too many invalid entries. Returning to the previous menu.")
    return None


def check_all_features(username):
    """Try every feature in FEATURES so the demo shows a full report."""
    for feature_key in FEATURES:
        report_feature_access(username, feature_key)


def run_session(username, passwords):
    """One person's story: log in, greet them, check features, show inbox."""
    print("")
    print("--- Session: {0} ---".format(username))
    print("Logging in user: {0} ...".format(username))

    success, message = login_with_retries(username, passwords)
    if not success:
        print("FAILED ({0})".format(message))
        # Lockout messages are stored on the account; unknown users have none.
        if username in USERS:
            show_notifications(username)
        print(SEPARATOR)
        return False

    print("SUCCESS")
    welcome_user(username)
    check_all_features(username)
    show_notifications(username)
    print(SEPARATOR)
    return True


def run_demo():
    """Seven scripted logins that cover the main success and failure paths."""
    # Always start from the factory data and never touch data/users.json,
    # so every demo run (and every screenshot) looks the same.
    use_seed_data()
    print("=== Learning Platform Access System ===")

    # 1. Subscribed student: quizzes + grades granted, analytics denied.
    run_session("student_alex", ["alex123"])

    # 2. Same role, expired plan: quizzes/grades blocked by subscription.
    run_session("student_sam", ["sam123"])

    # 3. Subscribed instructor: analytics granted, admin config denied.
    run_session("prof_jordan", ["jordan123"])

    # 4. Retry logic: first guess is wrong, second guess works.
    run_session("prof_lee", ["wrong", "lee123"])

    # 5. Admin with no subscription still gets every feature.
    run_session("admin_casey", ["admin123"])

    # 6. Three bad passwords lock Alex. This is a new attempt after step 1.
    run_session("student_alex", ["a", "b", "c"])

    # 7. Name is not in USERS, so we do not spend password retries.
    run_session("ghost_user", ["x"])


def interactive_feature_menu(username):
    """Let the user pick one feature by number, or go back."""
    keys = list(FEATURES.keys())
    print("")
    print("Choose a feature:")
    for index, key in enumerate(keys, start=1):
        label = FEATURES[key].get("label", key)
        print("  {0}) {1}".format(index, label))
    print("  {0}) Back".format(len(keys) + 1))

    valid = [str(i) for i in range(1, len(keys) + 2)]
    choice = prompt_choice("Feature number: ", valid)
    if choice is None:
        return
    if choice == str(len(keys) + 1):
        return

    feature_key = keys[int(choice) - 1]
    report_feature_access(username, feature_key)


def admin_unlock_menu():
    """Admin only: pick a locked account and unlock it."""
    locked = [name for name, record in USERS.items() if record.get("locked")]
    if not locked:
        print("No accounts are locked.")
        return

    print("")
    print("Locked accounts:")
    for index, name in enumerate(locked, start=1):
        print("  {0}) {1}".format(index, name))
    print("  {0}) Back".format(len(locked) + 1))

    valid = [str(i) for i in range(1, len(locked) + 2)]
    choice = prompt_choice("Account number: ", valid)
    if choice is None or choice == str(len(locked) + 1):
        return

    target = locked[int(choice) - 1]
    unlock_account(target)
    print("Unlocked {0}.".format(target))


def is_admin(username):
    """Reuse the real access rule: admins are the ones who may open admin_config."""
    user = USERS.get(username) or {}
    granted, _ = evaluate_access(
        True, user.get("role"), bool(user.get("has_active_subscription")),
        "admin_config",
    )
    return granted


def interactive_main_menu(username):
    """Loop until logout (or too many invalid menu choices)."""
    admin = is_admin(username)
    while True:
        print("")
        print("Main menu:")
        print("  1) Access a feature")
        print("  2) View notifications")
        print("  3) Logout")
        valid = ["1", "2", "3"]
        if admin:
            print("  4) Unlock a locked account (admin)")
            valid.append("4")
        choice = prompt_choice("Select 1-{0}: ".format(len(valid)), valid)
        if choice is None:
            return
        if choice == "1":
            interactive_feature_menu(username)
        elif choice == "2":
            show_notifications(username)
        elif choice == "4":
            admin_unlock_menu()
        else:
            print("Logged out.")
            return


def run_interactive():
    """Type a real username/password instead of using the canned demo list."""
    status = enable_persistence()
    print("=== Learning Platform Access System ===")
    if status == "created":
        print("Created a new save file: {0}".format(os.path.normpath(DATA_FILE)))
    elif status == "recovered":
        print("The save file was unreadable. It was backed up as users.json.corrupt")
        print("and fresh data was created.")
    else:
        print("Loaded saved data from {0}".format(os.path.normpath(DATA_FILE)))
    print("Type 'quit' at the username prompt to exit.")

    while True:
        username = _safe_input("\nUsername (or 'quit' to exit): ")
        if username.lower() == "quit":
            print("Goodbye.")
            return
        if username == "":
            print("Please enter a username.")
            continue

        success, message = interactive_password_login(username, _safe_input)
        if not success:
            print("FAILED ({0})".format(message))
            if username in USERS:
                show_notifications(username)
            continue

        print("SUCCESS")
        welcome_user(username)
        interactive_main_menu(username)


def main(argv):
    """Choose demo or interactive, and never show a raw traceback."""
    try:
        flags = argv[1:]
        if "--reset" in flags:
            enable_persistence()
            reset_data()
            print("Saved data was reset to the starting accounts.")
        if "--interactive" in flags:
            run_interactive()
        else:
            run_demo()
    except KeyboardInterrupt:
        # Ctrl+C
        print("\nGoodbye.")
    except EOFError:
        # No more input (closed terminal / piped stdin).
        print("\nGoodbye.")


if __name__ == "__main__":
    main(sys.argv)