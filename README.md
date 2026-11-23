# Contact Management System

An offline, secure desktop **Contact Management System** developed in **Python 3.10+**, **Tkinter (ttk)**, and **SQLite 3** as a BCA College Project (Uttaranchal University).

---

## 1. Project Introduction & Objectives

People and small offices often store contacts across phone memory, paper diaries, spreadsheets, and chat apps—leading to duplicates, slow searches, and data loss. This desktop application centralizes all contact records in a single password-protected local SQLite database without requiring an internet connection or external server.

**Key Objectives:**
- Store contact details (Name, Phone, Email, Address, Group) in an organized local SQLite database.
- Provide fast keyword search and group filtering (under 1 second for up to 10,000 contacts).
- Organize contacts into user-defined groups with a default `General` group.
- Secure data with salted `PBKDF2-HMAC-SHA256` password hashing, 3-attempt account lockout, 10-minute session timeout, and role-based access control (`Admin` / `User`).
- Support UTF-8 CSV Import/Export and timestamped SQLite Database Backup & Restore.
- Generate 7 official reports with CSV export and printing support.

---

## 2. Technology Stack

| Component | Technology |
| :--- | :--- |
| Programming Language | Python 3.10 or higher |
| GUI Framework | Tkinter with `ttk` widgets |
| Database | SQLite 3 (`contacts.db`) |
| Database Module | Built-in `sqlite3` |
| Password Security | `hashlib` (PBKDF2-HMAC-SHA256 + random salt) |
| Data Import / Export | Built-in `csv` module (UTF-8) |
| Testing | Built-in `unittest` module |
| Packaging (Optional) | PyInstaller (`.exe`) |

---

## 3. Three-Layer Architecture & Folder Structure

1. **Presentation Layer (`ui.py`)**: Light-themed Navy Blue, White, and Subtle Grey Tkinter GUI.
2. **Application Logic Layer (`auth.py`, `users.py`, `groups.py`, `contacts.py`, `import_export.py`, `backup.py`, `reports.py`)**: Validation, security rules, and business logic.
3. **Data Layer (`database.py`)**: SQLite connection, schema initialization (4 tables), parameterized queries, and backup/restore.

```text
Contact-Management-System/
├── main.py              # Application entry point
├── database.py          # SQLite Data Layer (4 tables, foreign keys, backup/restore)
├── auth.py              # Login, PBKDF2 verification, 3-attempt lock, 10-min timeout
├── users.py             # Module 1: Admin User Management
├── groups.py            # Module 2: Group Management
├── contacts.py          # Module 3 & 4: Contact CRUD, Validation, Search & Filter
├── import_export.py     # Module 5A & 5B: UTF-8 CSV Import & Export
├── backup.py            # Module 5C, 5D & 5E: DB Backup, Admin Restore & History
├── reports.py           # Module 6: 7 Official Reports + CSV Export & Print
├── ui.py                # Tkinter + ttk Desktop Interface
├── requirements.txt     # Dependencies list
├── README.md            # Project documentation
└── tests/
    └── test_cms.py      # 20 automated unit tests (isolated test DB)
```

---

## 4. Database Schema (4 Tables)

- **`users`**: `user_id` (PK), `username` (Unique), `password_hash`, `role` (`Admin`/`User`), `created_on`
- **`groups`**: `group_id` (PK), `group_name` (Unique), `description`
- **`contacts`**: `contact_id` (PK), `first_name`, `last_name`, `phone` (10 digits), `email`, `address`, `group_id` (FK -> `groups`), `user_id` (FK -> `users`), `created_on`
- **`backup_log`**: `log_id` (PK), `backup_date`, `file_name`, `user_id` (FK -> `users`)

---

## 5. Installation & Execution

### Prerequisites
- Install **Python 3.10+** (ensure **"Add Python to PATH"** is checked during installation).
- Open the project folder in **Visual Studio Code**.

### Run the Application
No external packages are required to run the core application:

```bash
git clone <repository-url>
cd Contact-Management-System
python main.py
```

On first launch, `contacts.db`, the default `General` group, `backups/`, `reports/`, and the default Admin account are created automatically.

### Default Admin Credentials
- **Username:** `admin`
- **Password:** `Admin@123`

*(Change or reset the password after first login via User Management.)*

---

## 6. Six Project Modules

1. **Login & User Management**: Salted PBKDF2-HMAC-SHA256 login, 5-minute lock after 3 failed attempts, 10-minute inactivity auto-logout, and Admin-only user CRUD + password reset.
2. **Group Management**: Create, view, rename, and delete groups (Admin only). Deleting a group automatically moves its contacts to `General`.
3. **Contact Management**: Full CRUD with mandatory First Name & 10-digit Phone validation, email format check, duplicate phone detection, and delete confirmation.
4. **Search & Filter**: Live SQLite `LIKE` search across First Name, Last Name, Phone, and Email combined with Group filtering and alphabetical sorting.
5. **Import / Export / Backup**: UTF-8 CSV import with summary stats (processed, imported, skipped duplicates, invalid), UTF-8 CSV export, timestamped SQLite backups, Admin-only restore, and backup history log.
6. **Reports**:
   1. All Contacts List (Alphabetical)
   2. Group-wise Contact List
   3. Incomplete Contacts (Missing Email or Address)
   4. Recently Added Contacts (Last 30 Days)
   5. Possible Duplicate Contacts
   6. Backup History Report
   7. User List (Admin only)

---

## 7. Running Unit Tests

Run all 20 automated test cases (uses a temporary isolated database):

```bash
python -m unittest discover -s tests -v
```

---

## 8. Packaging as a Windows `.exe` (PyInstaller)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "ContactManagementSystem" main.py
```

The standalone executable will be generated inside the `dist/` folder.

---

## 9. Security Mechanisms & Future Scope

**Security:** Salted PBKDF2-HMAC-SHA256 hashing, 3-attempt account lock, 10-minute inactivity timeout, role-based access control, input validation, parameterized SQL queries, and foreign key integrity.

**Future Scope:** Mobile companion sync, encrypted cloud backup, vCard (`.vcf`) import/export, direct SMS/Email/WhatsApp messaging, automatic duplicate merging, and multi-user network database support.
