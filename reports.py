"""
reports.py - Module 6: Report Generation
Generates all 7 reports specified in the synopsis, supports CSV export (UTF-8),
and provides cross-platform text printing support.
"""

import csv
import os
import subprocess
import sys
import tempfile
from database import DatabaseManager, REPORTS_DIR


class ReportGenerator:
    """Generates the 7 official reports from SQLite and exports/prints them."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def all_contacts(self) -> tuple[list[str], list[tuple]]:
        """Report 1: All Contacts List (Alphabetical)."""
        headers = [
            "Contact ID", "First Name", "Last Name", "Phone",
            "Email", "Address", "Group", "Created On",
        ]
        rows = self.db.fetchall(
            """
            SELECT c.contact_id, c.first_name, COALESCE(c.last_name, ''), c.phone,
                   COALESCE(c.email, ''), COALESCE(c.address, ''), g.group_name, c.created_on
            FROM contacts c
            JOIN groups g ON c.group_id = g.group_id
            ORDER BY c.first_name COLLATE NOCASE ASC, c.last_name COLLATE NOCASE ASC;
            """
        )
        return headers, rows

    def group_wise(self, group_id: int | None = None) -> tuple[list[str], list[tuple]]:
        """Report 2: Group-wise Contact List (all groups or filtered by group_id)."""
        headers = [
            "Group", "Contact ID", "First Name", "Last Name",
            "Phone", "Email", "Address",
        ]
        if group_id is not None:
            rows = self.db.fetchall(
                """
                SELECT g.group_name, c.contact_id, c.first_name, COALESCE(c.last_name, ''),
                       c.phone, COALESCE(c.email, ''), COALESCE(c.address, '')
                FROM contacts c
                JOIN groups g ON c.group_id = g.group_id
                WHERE c.group_id = ?
                ORDER BY c.first_name COLLATE NOCASE ASC, c.last_name COLLATE NOCASE ASC;
                """,
                (group_id,),
            )
        else:
            rows = self.db.fetchall(
                """
                SELECT g.group_name, c.contact_id, c.first_name, COALESCE(c.last_name, ''),
                       c.phone, COALESCE(c.email, ''), COALESCE(c.address, '')
                FROM contacts c
                JOIN groups g ON c.group_id = g.group_id
                ORDER BY g.group_name COLLATE NOCASE ASC,
                         c.first_name COLLATE NOCASE ASC,
                         c.last_name COLLATE NOCASE ASC;
                """
            )
        return headers, rows

    def incomplete_contacts(self) -> tuple[list[str], list[tuple]]:
        """Report 3: Incomplete Contacts (Missing Email or Address)."""
        headers = [
            "Contact ID", "First Name", "Last Name", "Phone",
            "Email", "Address", "Group",
        ]
        rows = self.db.fetchall(
            """
            SELECT c.contact_id, c.first_name, COALESCE(c.last_name, ''), c.phone,
                   COALESCE(c.email, ''), COALESCE(c.address, ''), g.group_name
            FROM contacts c
            JOIN groups g ON c.group_id = g.group_id
            WHERE TRIM(COALESCE(c.email, '')) = '' OR TRIM(COALESCE(c.address, '')) = ''
            ORDER BY c.first_name COLLATE NOCASE ASC, c.last_name COLLATE NOCASE ASC;
            """
        )
        return headers, rows

    def recently_added(self, days: int = 30) -> tuple[list[str], list[tuple]]:
        """Report 4: Recently Added Contacts (Default: Last 30 Days)."""
        headers = [
            "Contact ID", "First Name", "Last Name", "Phone",
            "Email", "Group", "Created On",
        ]
        rows = self.db.fetchall(
            """
            SELECT c.contact_id, c.first_name, COALESCE(c.last_name, ''), c.phone,
                   COALESCE(c.email, ''), g.group_name, c.created_on
            FROM contacts c
            JOIN groups g ON c.group_id = g.group_id
            WHERE c.created_on >= DATE('now', ?)
            ORDER BY c.created_on DESC, c.contact_id DESC;
            """,
            (f"-{int(days)} days",),
        )
        return headers, rows

    def possible_duplicates(self) -> tuple[list[str], list[tuple]]:
        """Report 5: Possible Duplicate Contacts (same phone or same full name)."""
        headers = [
            "Contact ID", "First Name", "Last Name", "Phone",
            "Email", "Group", "Reason",
        ]
        rows = self.db.fetchall(
            """
            SELECT c.contact_id, c.first_name, COALESCE(c.last_name, ''), c.phone,
                   COALESCE(c.email, ''), g.group_name,
                   CASE
                       WHEN c.phone IN (
                           SELECT phone FROM contacts GROUP BY phone HAVING COUNT(*) > 1
                       ) THEN 'Duplicate Phone'
                       ELSE 'Duplicate Name'
                   END AS reason
            FROM contacts c
            JOIN groups g ON c.group_id = g.group_id
            WHERE c.phone IN (
                SELECT phone FROM contacts GROUP BY phone HAVING COUNT(*) > 1
            )
            OR LOWER(TRIM(c.first_name) || ' ' || TRIM(COALESCE(c.last_name, ''))) IN (
                SELECT LOWER(TRIM(first_name) || ' ' || TRIM(COALESCE(last_name, '')))
                FROM contacts
                GROUP BY LOWER(TRIM(first_name) || ' ' || TRIM(COALESCE(last_name, '')))
                HAVING COUNT(*) > 1
            )
            ORDER BY c.first_name COLLATE NOCASE ASC, c.phone ASC;
            """
        )
        return headers, rows

    def backup_history(self) -> tuple[list[str], list[tuple]]:
        """Report 6: Backup History Report."""
        headers = ["Backup ID", "Backup Date", "Backup Filename", "Performed By"]
        rows = self.db.fetchall(
            """
            SELECT b.log_id, b.backup_date, b.file_name, u.username
            FROM backup_log b
            JOIN users u ON b.user_id = u.user_id
            ORDER BY b.log_id DESC;
            """
        )
        return headers, rows

    def user_list(self, acting_role: str) -> tuple[list[str], list[tuple]]:
        """Report 7: User List (Admin only)."""
        if acting_role != "Admin":
            raise PermissionError("Access denied: Only Admin can view the User List report.")
        headers = ["User ID", "Username", "Role", "Created On"]
        rows = self.db.fetchall(
            "SELECT user_id, username, role, created_on FROM users ORDER BY user_id ASC;"
        )
        return headers, rows

    @staticmethod
    def export_csv(file_path: str, headers: list[str], rows: list[tuple]) -> str:
        """Export any generated report to a UTF-8 CSV file."""
        parent = os.path.dirname(file_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        else:
            os.makedirs(REPORTS_DIR, exist_ok=True)

        with open(file_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return file_path

    @staticmethod
    def print_report(title: str, headers: list[str], rows: list[tuple]) -> tuple[bool, str]:
        """Format report as plain text and send to default OS printer."""
        lines = [title, "=" * len(title), ""]
        lines.append(" | ".join(headers))
        lines.append("-" * (len(" | ".join(headers)) + 4))
        for row in rows:
            lines.append(" | ".join(str(v) for v in row))
        content = "\n".join(lines)

        tmp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", encoding="utf-8", delete=False
        )
        try:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        finally:
            tmp_file.close()

        try:
            if sys.platform.startswith("win"):
                os.startfile(tmp_path, "print")
                return True, "Report sent to default Windows printer."
            subprocess.run(["lp", tmp_path], check=True)
            return True, "Report sent to default printer."
        except Exception as exc:
            return False, f"Printing unavailable ({exc}). Saved printable text at: {tmp_path}"
