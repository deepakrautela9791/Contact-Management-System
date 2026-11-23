"""
main.py - Entry Point for Contact Management System
Run with: python main.py
"""

import tkinter as tk
from ui import ContactManagementApp


def main() -> None:
    root = tk.Tk()
    ContactManagementApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
