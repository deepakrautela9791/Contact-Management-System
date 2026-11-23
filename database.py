"""
database.py - Data Layer for Contact Management System
Handles SQLite 3 connection, schema creation (4 tables), default seeding,
parameterized queries, and safe backup/restore operations.
"""

import hashlib
import os
import sqlite3
from datetime import datetime


DEFAULT_DB_PATH = "contacts.db"
BACKUPS_DIR = "backups"
REPORTS_DIR = "reports"


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random 16-byte salt."""
    if salt is None:
        salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000,
    )
    return f"{salt.hex()}:{pwd_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plain-text password against a stored 'salt_hex:hash_hex' string."""
    try:
        salt_hex, hash_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = hash_password(password, salt)
        return hashlib.compare_digest(expected, stored_hash)
    except (ValueError, TypeError):
        return False


class DatabaseManager:
    """Manages all SQLite database operations for the Contact Management System."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.conn: sqlite3.Connection | None = None
        self._ensure_directories()
        self.initialize_database()

    def _ensure_directories(self) -> None:
        """Create required local directories if they do not exist."""
        os.makedirs(BACKUPS_DIR, exist_ok=True)
        os.makedirs(REPORTS_DIR, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        """Open a SQLite connection with foreign keys enabled."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA foreign_keys = ON;")
        return self.conn

    def close(self) -> None:
        """Close the active SQLite connection safely."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a parameterized write query (INSERT, UPDATE, DELETE) and commit."""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor
        except sqlite3.Error:
            conn.rollback()
            raise

    def fetchone(self, sql: str, params: tuple = ()):
        """Execute a parameterized SELECT query and return a single row."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchone()

    def fetchall(self, sql: str, params: tuple = ()) -> list[tuple]:
        """Execute a parameterized SELECT query and return all matching rows."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    def initialize_database(self) -> None:
        """Create the 4 required tables, default 'General' group, and default Admin user."""
        conn = self.connect()
        cursor = conn.cursor()

        # Table 1: users
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Admin', 'User')),
                created_on TEXT DEFAULT (DATE('now'))
            );
            """
        )

        # Table 2: groups
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT UNIQUE NOT NULL,
                description TEXT
            );
            """
        )

        # Table 3: contacts
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                phone TEXT NOT NULL,
                email TEXT,
                address TEXT,
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_on TEXT DEFAULT (DATE('now')),
                FOREIGN KEY (group_id) REFERENCES groups(group_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            """
        )

        # Table 4: backup_log
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS backup_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_date TEXT NOT NULL,
                file_name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            """
        )

        # Indexes for fast search (< 1s for up to 10,000 contacts)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(first_name, last_name);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone);"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_contacts_group ON contacts(group_id);"
        )

        # Seed default 'General' group
        cursor.execute(
            """
            INSERT OR IGNORE INTO groups (group_name, description)
            VALUES (?, ?);
            """,
            ("General", "Default contact group"),
        )

        # Seed default Admin account if no users exist
        cursor.execute("SELECT COUNT(*) FROM users;")
        if cursor.fetchone()[0] == 0:
            default_admin_hash = hash_password("Admin@123")
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?);
                """,
                ("admin", default_admin_hash, "Admin"),
            )

        conn.commit()

    def backup_db(self, user_id: int, backup_dir: str = BACKUPS_DIR) -> str:
        """Create a timestamped backup of the SQLite database and log it in backup_log."""
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"contacts_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, file_name)

        source_conn = self.connect()
        dest_conn = sqlite3.connect(backup_path)
        try:
            source_conn.backup(dest_conn)
        finally:
            dest_conn.close()

        backup_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.execute(
            """
            INSERT INTO backup_log (backup_date, file_name, user_id)
            VALUES (?, ?, ?);
            """,
            (backup_date, file_name, user_id),
        )
        return backup_path

    def restore_db(self, backup_file_path: str) -> None:
        """Safely restore the database from a validated SQLite backup file."""
        if not os.path.isfile(backup_file_path):
            raise FileNotFoundError("Selected backup file does not exist.")

        # Validate that the backup file is a valid SQLite DB with required tables
        required_tables = {"users", "groups", "contacts", "backup_log"}
        test_conn = sqlite3.connect(backup_file_path)
        try:
            cursor = test_conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = {row[0] for row in cursor.fetchall()}
            if not required_tables.issubset(existing_tables):
                raise ValueError(
                    "Invalid backup file: required tables are missing."
                )

            # Perform safe online restore into current database
            dest_conn = self.connect()
            test_conn.backup(dest_conn)
            dest_conn.execute("PRAGMA foreign_keys = ON;")
        finally:
            test_conn.close()
