"""
contacts.py - Module 3 (Contact Management) & Module 4 (Search and Filter)
Handles full CRUD operations, input validation, duplicate phone detection,
and fast SQLite keyword search + group filtering.
"""

import re
from database import DatabaseManager
from groups import GroupManager


PHONE_PATTERN = re.compile(r"^\d{10}$")
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class ContactManager:
    """Application logic for Contact CRUD, validation, and Search & Filter."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.group_manager = GroupManager(db)

    @staticmethod
    def validate_contact(
        first_name: str, phone: str, email: str = ""
    ) -> tuple[bool, str]:
        """Validate mandatory fields, 10-digit phone number, and optional email format."""
        if not first_name or not first_name.strip():
            return False, "First Name is mandatory."

        phone_clean = phone.strip() if phone else ""
        if not phone_clean:
            return False, "Phone Number is mandatory."
        if not PHONE_PATTERN.match(phone_clean):
            return False, "Phone Number must contain exactly 10 digits."

        email_clean = email.strip() if email else ""
        if email_clean and not EMAIL_PATTERN.match(email_clean):
            return False, "Invalid email format (example: user@example.com)."

        return True, ""

    def is_duplicate_phone(
        self, phone: str, exclude_contact_id: int | None = None
    ) -> bool:
        """Check if a phone number already exists in the contacts table."""
        phone_clean = phone.strip()
        if exclude_contact_id is not None:
            row = self.db.fetchone(
                "SELECT contact_id FROM contacts WHERE phone = ? AND contact_id != ?;",
                (phone_clean, exclude_contact_id),
            )
        else:
            row = self.db.fetchone(
                "SELECT contact_id FROM contacts WHERE phone = ?;",
                (phone_clean,),
            )
        return row is not None

    def add_contact(
        self,
        first_name: str,
        last_name: str,
        phone: str,
        email: str,
        address: str,
        group_id: int | None,
        user_id: int,
    ) -> tuple[bool, str]:
        """Validate and insert a new contact into SQLite."""
        valid, msg = self.validate_contact(first_name, phone, email)
        if not valid:
            return False, msg

        phone_clean = phone.strip()
        if self.is_duplicate_phone(phone_clean):
            return False, f"Duplicate contact: Phone number '{phone_clean}' already exists."

        if group_id is None:
            group_id = self.group_manager.get_default_group_id()

        self.db.execute(
            """
            INSERT INTO contacts (first_name, last_name, phone, email, address, group_id, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                first_name.strip(),
                (last_name or "").strip(),
                phone_clean,
                (email or "").strip(),
                (address or "").strip(),
                group_id,
                user_id,
            ),
        )
        return True, "Contact added successfully."

    def update_contact(
        self,
        contact_id: int,
        first_name: str,
        last_name: str,
        phone: str,
        email: str,
        address: str,
        group_id: int | None,
    ) -> tuple[bool, str]:
        """Validate and update an existing contact record."""
        existing = self.db.fetchone(
            "SELECT contact_id FROM contacts WHERE contact_id = ?;", (contact_id,)
        )
        if existing is None:
            return False, "Contact not found."

        valid, msg = self.validate_contact(first_name, phone, email)
        if not valid:
            return False, msg

        phone_clean = phone.strip()
        if self.is_duplicate_phone(phone_clean, exclude_contact_id=contact_id):
            return False, f"Duplicate contact: Phone number '{phone_clean}' already exists."

        if group_id is None:
            group_id = self.group_manager.get_default_group_id()

        self.db.execute(
            """
            UPDATE contacts
            SET first_name = ?, last_name = ?, phone = ?, email = ?, address = ?, group_id = ?
            WHERE contact_id = ?;
            """,
            (
                first_name.strip(),
                (last_name or "").strip(),
                phone_clean,
                (email or "").strip(),
                (address or "").strip(),
                group_id,
                contact_id,
            ),
        )
        return True, "Contact updated successfully."

    def delete_contact(self, contact_id: int) -> tuple[bool, str]:
        """Delete a contact by ID."""
        existing = self.db.fetchone(
            "SELECT contact_id FROM contacts WHERE contact_id = ?;", (contact_id,)
        )
        if existing is None:
            return False, "Contact not found."

        self.db.execute("DELETE FROM contacts WHERE contact_id = ?;", (contact_id,))
        return True, "Contact deleted successfully."

    def get_contact_by_id(self, contact_id: int):
        """Fetch a single contact record with its group name."""
        return self.db.fetchone(
            """
            SELECT c.contact_id, c.first_name, COALESCE(c.last_name, ''), c.phone,
                   COALESCE(c.email, ''), COALESCE(c.address, ''), c.group_id,
                   g.group_name, c.user_id, c.created_on
            FROM contacts c
            JOIN groups g ON c.group_id = g.group_id
            WHERE c.contact_id = ?;
            """,
            (contact_id,),
        )

    def get_all_contacts(self) -> list[tuple]:
        """Return all contacts sorted alphabetically by first_name, last_name."""
        return self.search_contacts(keyword="", group_id=None)

    def search_contacts(
        self, keyword: str = "", group_id: int | None = None
    ) -> list[tuple]:
        """
        Search contacts by First Name, Last Name, Phone, or Email,
        optionally filtered by group_id, sorted alphabetically by name.
        """
        query = """
            SELECT c.contact_id, c.first_name, COALESCE(c.last_name, ''), c.phone,
                   COALESCE(c.email, ''), COALESCE(c.address, ''), g.group_name,
                   c.user_id, c.created_on
            FROM contacts c
            JOIN groups g ON c.group_id = g.group_id
            WHERE 1=1
        """
        params: list = []

        kw = (keyword or "").strip()
        if kw:
            like_kw = f"%{kw}%"
            query += """
                AND (
                    c.first_name LIKE ?
                    OR c.last_name LIKE ?
                    OR c.phone LIKE ?
                    OR c.email LIKE ?
                )
            """
            params.extend([like_kw, like_kw, like_kw, like_kw])

        if group_id is not None:
            query += " AND c.group_id = ?"
            params.append(group_id)

        query += " ORDER BY c.first_name COLLATE NOCASE ASC, c.last_name COLLATE NOCASE ASC;"
        return self.db.fetchall(query, tuple(params))

    def get_dashboard_stats(self) -> dict:
        """Return summary counts for the dashboard cards."""
        total_contacts = self.db.fetchone("SELECT COUNT(*) FROM contacts;")[0]
        total_groups = self.db.fetchone("SELECT COUNT(*) FROM groups;")[0]
        total_users = self.db.fetchone("SELECT COUNT(*) FROM users;")[0]
        recent_contacts = self.db.fetchone(
            "SELECT COUNT(*) FROM contacts WHERE created_on >= DATE('now', '-30 days');"
        )[0]
        return {
            "total_contacts": total_contacts,
            "total_groups": total_groups,
            "total_users": total_users,
            "recent_contacts": recent_contacts,
        }
