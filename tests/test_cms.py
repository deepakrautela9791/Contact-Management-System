"""
tests/test_cms.py - Automated Unit Test Suite (20 Test Cases)
Uses Python's built-in unittest module with an isolated temporary SQLite database
so actual application data is never modified.
Run with: python -m unittest discover -s tests -v
"""

import csv
import os
import shutil
import tempfile
import unittest

from auth import AuthManager
from backup import BackupManager
from contacts import ContactManager
from database import DatabaseManager, hash_password, verify_password
from groups import GroupManager
from import_export import ImportExportManager
from reports import ReportGenerator
from users import UserManager


class TestContactManagementSystem(unittest.TestCase):
    """Covers all 20 required test cases from the project specification."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="cms_test_")
        self.db_path = os.path.join(self.temp_dir, "test_contacts.db")
        self.backup_dir = os.path.join(self.temp_dir, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

        self.db = DatabaseManager(db_path=self.db_path)
        self.auth = AuthManager(self.db)
        self.users = UserManager(self.db)
        self.groups = GroupManager(self.db)
        self.contacts = ContactManager(self.db)
        self.ie = ImportExportManager(self.db)
        self.backup = BackupManager(self.db)
        self.reports = ReportGenerator(self.db)

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # 1. Database initialization
    def test_01_database_initialization(self):
        tables = {
            row[0]
            for row in self.db.fetchall(
                "SELECT name FROM sqlite_master WHERE type='table';"
            )
        }
        self.assertTrue({"users", "groups", "contacts", "backup_log"}.issubset(tables))
        self.assertIsNotNone(self.groups.get_group_by_name("General"))
        admin = self.db.fetchone("SELECT username, role FROM users WHERE username = 'admin';")
        self.assertEqual(admin, ("admin", "Admin"))

    # 2. Admin login
    def test_02_admin_login(self):
        ok, _ = self.auth.login("admin", "Admin@123")
        self.assertTrue(ok)
        self.assertTrue(self.auth.is_logged_in())
        self.assertTrue(self.auth.is_admin())

    # 3. Invalid login
    def test_03_invalid_login(self):
        ok, msg = self.auth.login("admin", "WrongPass")
        self.assertFalse(ok)
        self.assertIn("Invalid", msg)
        self.assertFalse(self.auth.is_logged_in())

    # 4. Password hashing and verification
    def test_04_password_hashing_and_verification(self):
        h1 = hash_password("Secret@123")
        h2 = hash_password("Secret@123")
        self.assertNotEqual(h1, h2)
        self.assertNotIn("Secret@123", h1)
        self.assertTrue(verify_password("Secret@123", h1))
        self.assertFalse(verify_password("Wrong@123", h1))

    # 5. Account lock after 3 failed attempts
    def test_05_account_lock_after_3_failed_attempts(self):
        self.auth.login("admin", "bad1")
        self.auth.login("admin", "bad2")
        ok, msg = self.auth.login("admin", "bad3")
        self.assertFalse(ok)
        self.assertIn("locked", msg.lower())
        ok_locked, msg_locked = self.auth.login("admin", "Admin@123")
        self.assertFalse(ok_locked)
        self.assertIn("locked", msg_locked.lower())

    # 6. User creation and management
    def test_06_user_creation_and_management(self):
        ok, _ = self.users.create_user("staff1", "Pass@123", "User", "Admin")
        self.assertTrue(ok)
        all_u = self.users.list_users()
        staff = [u for u in all_u if u[1] == "staff1"][0]
        ok_edit, _ = self.users.edit_user(staff[0], "staff_updated", "Admin", "Admin")
        self.assertTrue(ok_edit)
        ok_reset, _ = self.users.reset_password(staff[0], "NewPass@123", "Admin")
        self.assertTrue(ok_reset)
        ok_login, _ = self.auth.login("staff_updated", "NewPass@123")
        self.assertTrue(ok_login)
        ok_del, _ = self.users.delete_user(staff[0], acting_user_id=1, acting_role="Admin")
        self.assertTrue(ok_del)

    # 7. Group creation and deletion (contacts move to General)
    def test_07_group_creation_and_deletion(self):
        ok, _ = self.groups.add_group("Clients", "Business clients")
        self.assertTrue(ok)
        grp_id = self.groups.get_group_by_name("Clients")[0]
        self.contacts.add_contact("Amit", "Verma", "9876543210", "amit@example.com", "Delhi", grp_id, 1)
        ok_del, _ = self.groups.delete_group(grp_id, acting_role="Admin")
        self.assertTrue(ok_del)
        contact = self.contacts.get_all_contacts()[0]
        self.assertEqual(contact[6], "General")

    # 8. Contact creation
    def test_08_contact_creation(self):
        ok, _ = self.contacts.add_contact("Rahul", "Sharma", "9123456789", "rahul@example.com", "Aligarh", None, 1)
        self.assertTrue(ok)
        rows = self.contacts.get_all_contacts()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][1], "Rahul")

    # 9. Contact editing
    def test_09_contact_editing(self):
        self.contacts.add_contact("Neha", "Singh", "9988776655", "", "", None, 1)
        cid = self.contacts.get_all_contacts()[0][0]
        ok, _ = self.contacts.update_contact(cid, "Neha", "Gupta", "9988776655", "neha@example.com", "Mathura", None)
        self.assertTrue(ok)
        updated = self.contacts.get_contact_by_id(cid)
        self.assertEqual(updated[2], "Gupta")
        self.assertEqual(updated[4], "neha@example.com")

    # 10. Contact deletion
    def test_10_contact_deletion(self):
        self.contacts.add_contact("Vikas", "Yadav", "9000011111", "", "", None, 1)
        cid = self.contacts.get_all_contacts()[0][0]
        ok, _ = self.contacts.delete_contact(cid)
        self.assertTrue(ok)
        self.assertEqual(len(self.contacts.get_all_contacts()), 0)

    # 11. Phone number validation
    def test_11_phone_number_validation(self):
        ok_short, _ = self.contacts.add_contact("Test", "", "12345", "", "", None, 1)
        ok_alpha, _ = self.contacts.add_contact("Test", "", "98765abcde", "", "", None, 1)
        self.assertFalse(ok_short)
        self.assertFalse(ok_alpha)

    # 12. Email validation
    def test_12_email_validation(self):
        ok_bad, _ = self.contacts.add_contact("Test", "", "9876543211", "invalid-email", "", None, 1)
        self.assertFalse(ok_bad)
        ok_good, _ = self.contacts.add_contact("Test", "", "9876543211", "valid@example.com", "", None, 1)
        self.assertTrue(ok_good)

    # 13. Duplicate contact detection
    def test_13_duplicate_contact_detection(self):
        self.contacts.add_contact("First", "", "9111122222", "", "", None, 1)
        ok_dup, msg = self.contacts.add_contact("Second", "", "9111122222", "", "", None, 1)
        self.assertFalse(ok_dup)
        self.assertIn("Duplicate", msg)

    # 14. Search and filtering
    def test_14_search_and_filtering(self):
        self.groups.add_group("Family")
        fam_id = self.groups.get_group_by_name("Family")[0]
        self.contacts.add_contact("Ankit", "Kumar", "9012345678", "ankit@mail.com", "", fam_id, 1)
        self.contacts.add_contact("Priya", "Jain", "9012345679", "priya@mail.com", "", None, 1)
        by_name = self.contacts.search_contacts(keyword="Ankit")
        self.assertEqual(len(by_name), 1)
        by_group = self.contacts.search_contacts(group_id=fam_id)
        self.assertEqual(len(by_group), 1)
        self.assertEqual(by_group[0][1], "Ankit")

    # 15. CSV import
    def test_15_csv_import(self):
        csv_path = os.path.join(self.temp_dir, "import.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["First Name", "Last Name", "Phone", "Email", "Address", "Group"])
            writer.writerow(["Suresh", "Raina", "9876500001", "suresh@mail.com", "UP", "Friends"])
            writer.writerow(["Suresh", "Dup", "9876500001", "", "", "Friends"])
            writer.writerow(["Invalid", "User", "123", "", "", "General"])
        summary = self.ie.import_contacts_csv(csv_path, user_id=1)
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["imported"], 1)
        self.assertEqual(summary["duplicates"], 1)
        self.assertEqual(summary["invalid"], 1)

    # 16. CSV export
    def test_16_csv_export(self):
        self.contacts.add_contact("Deepak", "Rautela", "9876543219", "deepak@mail.com", "UP", None, 1)
        out_path = os.path.join(self.temp_dir, "export.csv")
        count = self.ie.export_contacts_csv(out_path)
        self.assertEqual(count, 1)
        self.assertTrue(os.path.isfile(out_path))

    # 17. Database backup
    def test_17_database_backup(self):
        ok, backup_path = self.backup.create_backup(user_id=1, backup_dir=self.backup_dir)
        self.assertTrue(ok)
        self.assertTrue(os.path.isfile(backup_path))
        history = self.backup.get_backup_history()
        self.assertEqual(len(history), 1)

    # 18. Database restore
    def test_18_database_restore(self):
        self.contacts.add_contact("Before", "Backup", "9876511111", "", "", None, 1)
        ok, backup_path = self.backup.create_backup(user_id=1, backup_dir=self.backup_dir)
        self.assertTrue(ok)
        cid = self.contacts.get_all_contacts()[0][0]
        self.contacts.delete_contact(cid)
        self.assertEqual(len(self.contacts.get_all_contacts()), 0)
        ok_res, _ = self.backup.restore_backup(backup_path, acting_role="Admin")
        self.assertTrue(ok_res)
        self.assertEqual(len(self.contacts.get_all_contacts()), 1)

    # 19. Report generation
    def test_19_report_generation(self):
        self.contacts.add_contact("Rohan", "Das", "9876522222", "", "", None, 1)
        _, all_rows = self.reports.all_contacts()
        _, grp_rows = self.reports.group_wise()
        _, inc_rows = self.reports.incomplete_contacts()
        _, rec_rows = self.reports.recently_added(30)
        _, dup_rows = self.reports.possible_duplicates()
        _, bkp_rows = self.reports.backup_history()
        _, usr_rows = self.reports.user_list("Admin")
        self.assertEqual(len(all_rows), 1)
        self.assertEqual(len(grp_rows), 1)
        self.assertEqual(len(inc_rows), 1)
        self.assertEqual(len(rec_rows), 1)
        self.assertEqual(len(dup_rows), 0)
        self.assertEqual(len(bkp_rows), 0)
        self.assertEqual(len(usr_rows), 1)

    # 20. Role-based access restrictions
    def test_20_role_based_access_restrictions(self):
        with self.assertRaises(PermissionError):
            self.users.create_user("hacker", "Pass@123", "Admin", acting_role="User")
        with self.assertRaises(PermissionError):
            self.groups.delete_group(1, acting_role="User")
        with self.assertRaises(PermissionError):
            self.backup.restore_backup("dummy.db", acting_role="User")
        with self.assertRaises(PermissionError):
            self.reports.user_list(acting_role="User")


if __name__ == "__main__":
    unittest.main()
