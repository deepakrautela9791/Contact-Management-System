"""
auth.py - Authentication & Session Security for Contact Management System
Implements PBKDF2-HMAC-SHA256 verification, 3-attempt / 5-minute account lock,
and 10-minute inactivity session timeout.
"""

from datetime import datetime, timedelta
from database import DatabaseManager, verify_password


MAX_FAILED_ATTEMPTS = 3
LOCK_DURATION_MINUTES = 5
SESSION_TIMEOUT_MINUTES = 10


class AuthManager:
    """Handles user login, lockout policy, and session inactivity tracking."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.current_user: dict | None = None
        self.last_activity: datetime | None = None
        # Tracks failed attempts in memory: {username: {"count": int, "locked_until": datetime | None}}
        self._login_attempts: dict[str, dict] = {}

    def _get_attempt_record(self, username: str) -> dict:
        key = username.strip().lower()
        if key not in self._login_attempts:
            self._login_attempts[key] = {"count": 0, "locked_until": None}
        return self._login_attempts[key]

    def get_lock_remaining_seconds(self, username: str) -> int:
        """Return remaining lock time in seconds, or 0 if not locked."""
        record = self._get_attempt_record(username)
        locked_until = record["locked_until"]
        if locked_until is None:
            return 0
        now = datetime.now()
        if now >= locked_until:
            record["count"] = 0
            record["locked_until"] = None
            return 0
        return int((locked_until - now).total_seconds()) + 1

    def login(self, username: str, password: str) -> tuple[bool, str]:
        """Authenticate a user against SQLite with 3-attempt / 5-minute lockout."""
        username = username.strip()
        if not username or not password:
            return False, "Username and password are required."

        remaining = self.get_lock_remaining_seconds(username)
        if remaining > 0:
            mins, secs = divmod(remaining, 60)
            return (
                False,
                f"Account is locked due to 3 failed attempts. Try again in {mins}m {secs}s.",
            )

        row = self.db.fetchone(
            "SELECT user_id, username, password_hash, role FROM users WHERE username = ?;",
            (username,),
        )

        if row is None or not verify_password(password, row[2]):
            record = self._get_attempt_record(username)
            record["count"] += 1
            if record["count"] >= MAX_FAILED_ATTEMPTS:
                record["locked_until"] = datetime.now() + timedelta(
                    minutes=LOCK_DURATION_MINUTES
                )
                return (
                    False,
                    f"Account locked for {LOCK_DURATION_MINUTES} minutes after {MAX_FAILED_ATTEMPTS} failed attempts.",
                )
            left = MAX_FAILED_ATTEMPTS - record["count"]
            return False, f"Invalid username or password. {left} attempt(s) remaining."

        # Successful login: reset attempt counter and start session
        record = self._get_attempt_record(username)
        record["count"] = 0
        record["locked_until"] = None

        self.current_user = {
            "user_id": row[0],
            "username": row[1],
            "role": row[3],
        }
        self.last_activity = datetime.now()
        return True, f"Welcome, {row[1]}!"

    def logout(self) -> None:
        """Clear the active user session."""
        self.current_user = None
        self.last_activity = None

    def is_logged_in(self) -> bool:
        """Return True if a user is currently authenticated."""
        return self.current_user is not None

    def is_admin(self) -> bool:
        """Return True if the logged-in user has the Admin role."""
        return self.current_user is not None and self.current_user["role"] == "Admin"

    def update_activity(self) -> None:
        """Refresh the last activity timestamp on user interaction."""
        if self.current_user is not None:
            self.last_activity = datetime.now()

    def is_session_expired(self) -> bool:
        """Return True if the user has been inactive for 10 minutes or more."""
        if self.current_user is None or self.last_activity is None:
            return False
        elapsed = datetime.now() - self.last_activity
        return elapsed >= timedelta(minutes=SESSION_TIMEOUT_MINUTES)
