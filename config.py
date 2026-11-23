"""Centralized configuration for the Contact Management System."""

from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "contacts.db"
ASSETS_DIR = BASE_DIR / "assets"
BACKUPS_DIR = BASE_DIR / "backups"
REPORTS_DIR = BASE_DIR / "reports"

# Application metadata
APP_TITLE = "Contact Management System"
APP_VERSION = "1.0.0"
DEFAULT_GROUP_NAME = "General"

# Security settings
PBKDF2_ITERATIONS = 100_000
MAX_FAILED_LOGIN_ATTEMPTS = 3
ACCOUNT_LOCK_MINUTES = 5
SESSION_TIMEOUT_MINUTES = 10

# UI Color Palette (Light Theme: Navy, Blue, White, Subtle Grey)
COLORS = {
    "navy": "#1B365D",
    "primary_blue": "#2563EB",
    "hover_blue": "#1D4ED8",
    "bg_white": "#FFFFFF",
    "bg_light": "#F8FAFC",
    "border_grey": "#CBD5E1",
    "text_dark": "#0F172A",
    "text_muted": "#475569",
    "danger": "#DC2626",
    "success": "#16A34A",
}
