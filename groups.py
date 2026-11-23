"""
groups.py - Module 2: Group Management
Handles creating, viewing, renaming, and deleting contact groups.
Maintains the default 'General' group and automatically moves contacts
to 'General' when a group is deleted.
"""

import sqlite3
from database import DatabaseManager


DEFAULT_GROUP_NAME = "General"


class GroupManager:
    """Application logic for managing contact groups."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_default_group_id(self) -> int:
        """Return the group_id of the default 'General' group, creating it if missing."""
        row = self.db.fetchone(
            "SELECT group_id FROM groups WHERE group_name = ?;",
            (DEFAULT_GROUP_NAME,),
        )
        if row is not None:
            return row[0]
        cursor = self.db.execute(
            "INSERT INTO groups (group_name, description) VALUES (?, ?);",
            (DEFAULT_GROUP_NAME, "Default contact group"),
        )
        return cursor.lastrowid

    def list_groups(self) -> list[tuple]:
        """Return all groups with their contact counts: (group_id, group_name, description, contact_count)."""
        return self.db.fetchall(
            """
            SELECT g.group_id, g.group_name, COALESCE(g.description, ''), COUNT(c.contact_id)
            FROM groups g
            LEFT JOIN contacts c ON g.group_id = c.group_id
            GROUP BY g.group_id, g.group_name, g.description
            ORDER BY CASE WHEN g.group_name = ? THEN 0 ELSE 1 END, g.group_name COLLATE NOCASE ASC;
            """,
            (DEFAULT_GROUP_NAME,),
        )

    def get_group_by_name(self, group_name: str):
        """Fetch a group row (group_id, group_name, description) by name (case-insensitive)."""
        return self.db.fetchone(
            "SELECT group_id, group_name, description FROM groups WHERE LOWER(group_name) = LOWER(?);",
            (group_name.strip(),),
        )

    def add_group(self, group_name: str, description: str = "") -> tuple[bool, str]:
        """Create a new contact group, preventing empty or duplicate names."""
        name = group_name.strip()
        desc = description.strip()
        if not name:
            return False, "Group name cannot be empty."

        if self.get_group_by_name(name) is not None:
            return False, f"Group '{name}' already exists."

        try:
            self.db.execute(
                "INSERT INTO groups (group_name, description) VALUES (?, ?);",
                (name, desc),
            )
            return True, f"Group '{name}' created successfully."
        except sqlite3.IntegrityError:
            return False, f"Group '{name}' already exists."

    def edit_group(
        self, group_id: int, new_name: str, description: str = ""
    ) -> tuple[bool, str]:
        """Rename an existing group or update its description."""
        name = new_name.strip()
        desc = description.strip()
        if not name:
            return False, "Group name cannot be empty."

        current = self.db.fetchone(
            "SELECT group_name FROM groups WHERE group_id = ?;", (group_id,)
        )
        if current is None:
            return False, "Group not found."

        if current[0] == DEFAULT_GROUP_NAME and name != DEFAULT_GROUP_NAME:
            return False, f"The default '{DEFAULT_GROUP_NAME}' group cannot be renamed."

        duplicate = self.db.fetchone(
            "SELECT group_id FROM groups WHERE LOWER(group_name) = LOWER(?) AND group_id != ?;",
            (name, group_id),
        )
        if duplicate is not None:
            return False, f"Group '{name}' already exists."

        try:
            self.db.execute(
                "UPDATE groups SET group_name = ?, description = ? WHERE group_id = ?;",
                (name, desc, group_id),
            )
            return True, f"Group updated to '{name}' successfully."
        except sqlite3.IntegrityError:
            return False, f"Group '{name}' already exists."

    def delete_group(
        self, group_id: int, acting_role: str = "Admin"
    ) -> tuple[bool, str]:
        """Delete a group (Admin only) and move its contacts to the default 'General' group."""
        if acting_role != "Admin":
            raise PermissionError("Access denied: Only Admin can delete groups.")

        current = self.db.fetchone(
            "SELECT group_name FROM groups WHERE group_id = ?;", (group_id,)
        )
        if current is None:
            return False, "Group not found."

        if current[0] == DEFAULT_GROUP_NAME:
            return False, f"The default '{DEFAULT_GROUP_NAME}' group cannot be deleted."

        default_id = self.get_default_group_id()

        # Move all contacts in this group to 'General' before deleting
        self.db.execute(
            "UPDATE contacts SET group_id = ? WHERE group_id = ?;",
            (default_id, group_id),
        )
        self.db.execute("DELETE FROM groups WHERE group_id = ?;", (group_id,))
        return (
            True,
            f"Group '{current[0]}' deleted. Its contacts were moved to '{DEFAULT_GROUP_NAME}'.",
        )
