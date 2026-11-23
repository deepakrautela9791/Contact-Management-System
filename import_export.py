"""
import_export.py - Module 5A & 5B: CSV Import and Export
Supports UTF-8 CSV import with validation, duplicate skipping, and summary stats,
as well as UTF-8 CSV export for all or selected contacts.
"""

import csv
import os
from contacts import ContactManager
from database import DatabaseManager
from groups import GroupManager


CSV_HEADERS = ["First Name", "Last Name", "Phone", "Email", "Address", "Group"]


class ImportExportManager:
    """Handles UTF-8 CSV import and export of contacts."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.contact_manager = ContactManager(db)
        self.group_manager = GroupManager(db)

    def import_contacts_csv(self, file_path: str, user_id: int) -> dict:
        """
        Import contacts from a UTF-8 CSV file.
        Returns a summary dict with total, imported, duplicates, invalid, and errors.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError("Selected CSV file does not exist.")

        summary = {
            "total": 0,
            "imported": 0,
            "duplicates": 0,
            "invalid": 0,
            "errors": [],
        }

        with open(file_path, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or missing header row.")

            # Normalize header names for flexible matching
            field_map = {h.strip().lower(): h for h in reader.fieldnames if h}

            def get_val(row: dict, *keys: str) -> str:
                for k in keys:
                    if k in field_map:
                        return (row.get(field_map[k]) or "").strip()
                return ""

            for row_num, row in enumerate(reader, start=2):
                summary["total"] += 1
                first_name = get_val(row, "first name", "first_name", "firstname", "name")
                last_name = get_val(row, "last name", "last_name", "lastname")
                phone = get_val(row, "phone", "phone number", "phone_number", "mobile")
                email = get_val(row, "email", "email address", "email_id")
                address = get_val(row, "address")
                group_name = get_val(row, "group", "group name", "group_name") or "General"

                valid, err_msg = self.contact_manager.validate_contact(
                    first_name, phone, email
                )
                if not valid:
                    summary["invalid"] += 1
                    summary["errors"].append(f"Row {row_num}: {err_msg}")
                    continue

                if self.contact_manager.is_duplicate_phone(phone):
                    summary["duplicates"] += 1
                    continue

                # Resolve or create group
                grp = self.group_manager.get_group_by_name(group_name)
                if grp is not None:
                    group_id = grp[0]
                else:
                    ok, _ = self.group_manager.add_group(group_name, "Created via CSV import")
                    if ok:
                        group_id = self.group_manager.get_group_by_name(group_name)[0]
                    else:
                        group_id = self.group_manager.get_default_group_id()

                ok, msg = self.contact_manager.add_contact(
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    email=email,
                    address=address,
                    group_id=group_id,
                    user_id=user_id,
                )
                if ok:
                    summary["imported"] += 1
                else:
                    summary["invalid"] += 1
                    summary["errors"].append(f"Row {row_num}: {msg}")

        return summary

    def export_contacts_csv(
        self, file_path: str, contacts: list[tuple] | None = None
    ) -> int:
        """
        Export given contacts (or all contacts if None) to a UTF-8 CSV file.
        Expected tuple format from ContactManager:
        (contact_id, first_name, last_name, phone, email, address, group_name, user_id, created_on)
        Returns the number of exported records.
        """
        if contacts is None:
            contacts = self.contact_manager.get_all_contacts()

        parent_dir = os.path.dirname(file_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(file_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
            for c in contacts:
                writer.writerow([c[1], c[2], c[3], c[4], c[5], c[6]])

        return len(contacts)
