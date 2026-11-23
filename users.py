"""
users.py - Module 1: User Management (Admin Only)
Allows Admin users to create, view, edit, delete users, change roles,
and reset passwords securely using PBKDF2-HMAC-SHA256.
"""

import sqlite3
from database import DatabaseManager, hash_password


VALID_ROLES = ("Admin", "User")


class UserManager:
    """Application logic for managing user accounts (Admin-only)."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def _require_admin(self, acting_role: str) -> None:
        if acting_role != "Admin":
            raise PermissionError("Access denied: Only Admin can manage user accounts.")

    def list_users(self) -> list[tuple]:
        """Return all users as (user_id, username, role, created_on)."""
        return self.db.fetchall(
            "SELECT user_id, username, role, created_on FROM users ORDER BY user_id ASC;"
        )

    def create_user(
        self, username: str, password: str, role: str, acting_role: str = "Admin"
    ) -> tuple[bool, str]:
        """Create a new user account with a salted PBKDF2-HMAC-SHA256 password hash."""
        self._require_admin(acting_role)
        username = username.strip()
        if not username:
            return False, "Username cannot be empty."
        if len(password) < 6:
            return False, "Password must be at least 6 characters long."
        if role not in VALID_ROLES:
            return False, "Role must be either 'Admin' or 'User'."

        password_hash = hash_password(password)
        try:
            self.db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?);",
                (username, password_hash, role),
            )
            return True, f"User '{username}' created successfully."
        except sqlite3.IntegrityError:
            return False, f"Username '{username}' already exists."

    def edit_user(
        self, user_id: int, username: str, role: str, acting_role: str = "Admin"
    ) -> tuple[bool, str]:
        """Update an existing user's username and role."""
        self._require_admin(acting_role)
        username = username.strip()
        if not username:
            return False, "Username cannot be empty."
        if role not in VALID_ROLES:
            return False, "Role must be either 'Admin' or 'User'."

        existing = self.db.fetchone(
            "SELECT role FROM users WHERE user_id = ?;", (user_id,)
        )
        if existing is None:
            return False, "User not found."

        # Prevent demoting the last remaining Admin
        if existing[0] == "Admin" and role != "Admin":
            admin_count = self.db.fetchone(
                "SELECT COUNT(*) FROM users WHERE role = 'Admin';"
            )[0]
            if admin_count <= 1:
                return False, "Cannot change role of the last remaining Admin."

        try:
            self.db.execute(
                "UPDATE users SET username = ?, role = ? WHERE user_id = ?;",
                (username, role, user_id),
            )
            return True, "User updated successfully."
        except sqlite3.IntegrityError:
            return False, f"Username '{username}' is already taken."

    def reset_password(
        self, user_id: int, new_password: str, acting_role: str = "Admin"
    ) -> tuple[bool, str]:
        """Reset a user's password with a new random salt and PBKDF2 hash."""
        self._require_admin(acting_role)
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters long."

        existing = self.db.fetchone(
            "SELECT user_id FROM users WHERE user_id = ?;", (user_id,)
        )
        if existing is None:
            return False, "User not found."

        new_hash = hash_password(new_password)
        self.db.execute(
            "UPDATE users SET password_hash = ? WHERE user_id = ?;",
            (new_hash, user_id),
        )
        return True, "Password reset successfully."

    def delete_user(
        self, user_id: int, acting_user_id: int, acting_role: str = "Admin"
    ) -> tuple[bool, str]:
        """Delete a user account after reassigning their contacts/backup logs to the acting Admin."""
        self._require_admin(acting_role)
        if user_id == acting_user_id:
            return False, "You cannot delete your own currently logged-in account."

        existing = self.db.fetchone(
            "SELECT role FROM users WHERE user_id = ?;", (user_id,)
        )
        if existing is None:
            return False, "User not found."

        if existing[0] == "Admin":
            admin_count = self.db.fetchone(
                "SELECT COUNT(*) FROM users WHERE role = 'Admin';"
            )[0]
            if admin_count <= 1:
                return False, "Cannot delete the last remaining Admin account."

        # Reassign dependent records to acting Admin to preserve foreign key integrity
        self.db.execute(
            "UPDATE contacts SET user_id = ? WHERE user_id = ?;",
            (acting_user_id, user_id),
        )
        self.db.execute(
            "UPDATE backup_log SET user_id = ? WHERE user_id = ?;",
            (acting_user_id, user_id),
        )
        self.db.execute("DELETE FROM users WHERE user_id = ?;", (user_id,))
        return True, "User deleted successfully."
