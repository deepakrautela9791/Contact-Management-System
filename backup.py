"""
backup.py - Module 5C, 5D & 5E: Database Backup, Restore, and Backup History
Creates timestamped SQLite backups, logs them in backup_log,
restricts database restoration to Admin users, and retrieves backup history.
"""

from database import BACKUPS_DIR, DatabaseManager


class BackupManager:
    """Application logic for database backup, restore, and backup history."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_backup(
        self, user_id: int, backup_dir: str = BACKUPS_DIR
    ) -> tuple[bool, str]:
        """Create a timestamped backup of contacts.db and record it in backup_log."""
        try:
            backup_path = self.db.backup_db(user_id=user_id, backup_dir=backup_dir)
            return True, backup_path
        except Exception as exc:
            return False, f"Backup failed: {exc}"

    def restore_backup(
        self, backup_file_path: str, acting_role: str
    ) -> tuple[bool, str]:
        """Restore contacts.db from a selected backup file (Admin only)."""
        if acting_role != "Admin":
            raise PermissionError("Access denied: Only Admin can restore database backups.")
        try:
            self.db.restore_db(backup_file_path)
            return True, "Database restored successfully."
        except Exception as exc:
            return False, f"Restore failed: {exc}"

    def get_backup_history(self) -> list[tuple]:
        """Return backup history as (log_id, backup_date, file_name, username)."""
        return self.db.fetchall(
            """
            SELECT b.log_id, b.backup_date, b.file_name, u.username
            FROM backup_log b
            JOIN users u ON b.user_id = u.user_id
            ORDER BY b.log_id DESC;
            """
        )
