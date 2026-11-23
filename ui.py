"""
ui.py - Presentation Layer for Contact Management System
Modern, light-themed Tkinter + ttk desktop interface (Navy Blue, White, Subtle Grey)
integrating all 6 official modules with role-based access control and session timeout.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from auth import AuthManager
from backup import BackupManager
from contacts import ContactManager
from database import DatabaseManager
from groups import GroupManager
from import_export import ImportExportManager
from reports import ReportGenerator
from users import UserManager


# Theme Palette (Navy Blue, White, Subtle Grey)
NAVY = "#1B365D"
NAVY_HOVER = "#264B7F"
WHITE = "#FFFFFF"
BG_GREY = "#F4F6F9"
BORDER_GREY = "#D8DEE6"
TEXT_DARK = "#1F2937"
TEXT_MUTED = "#6B7280"
DANGER = "#C0392B"
SUCCESS = "#1E8449"

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_HEADING = ("Segoe UI", 13, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_SMALL = ("Segoe UI", 9)


class ContactManagementApp:
    """Main desktop application controller for Contact Management System."""

    def __init__(self, root: tk.Tk, db: DatabaseManager | None = None):
        self.root = root
        self.root.title("Contact Management System")
        self.root.geometry("1180x720")
        self.root.minsize(1000, 640)
        self.root.configure(bg=BG_GREY)

        # Initialize layers
        self.db = db if db is not None else DatabaseManager()
        self.auth = AuthManager(self.db)
        self.user_mgr = UserManager(self.db)
        self.group_mgr = GroupManager(self.db)
        self.contact_mgr = ContactManager(self.db)
        self.ie_mgr = ImportExportManager(self.db)
        self.backup_mgr = BackupManager(self.db)
        self.report_gen = ReportGenerator(self.db)

        self._session_job = None
        self._active_nav_btn = None
        self._current_report_data: tuple[str, list[str], list[tuple]] = ("", [], [])

        self._configure_styles()
        self._bind_activity_events()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.show_login_screen()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            background=WHITE,
            foreground=TEXT_DARK,
            rowheight=28,
            fieldbackground=WHITE,
            font=FONT_BODY,
        )
        style.configure(
            "Treeview.Heading",
            background=NAVY,
            foreground=WHITE,
            font=FONT_BOLD,
            relief="flat",
        )
        style.map("Treeview.Heading", background=[("active", NAVY_HOVER)])
        style.map("Treeview", background=[("selected", "#D6E4F0")], foreground=[("selected", TEXT_DARK)])

    def _bind_activity_events(self) -> None:
        for seq in ("<Any-KeyPress>", "<ButtonPress>", "<Motion>"):
            self.root.bind_all(seq, lambda _e: self.auth.update_activity())

    def _start_session_monitor(self) -> None:
        self._stop_session_monitor()
        self._check_session_timeout()

    def _stop_session_monitor(self) -> None:
        if self._session_job is not None:
            self.root.after_cancel(self._session_job)
            self._session_job = None

    def _check_session_timeout(self) -> None:
        if self.auth.is_logged_in():
            if self.auth.is_session_expired():
                self.auth.logout()
                messagebox.showwarning(
                    "Session Expired",
                    "You have been logged out automatically due to 10 minutes of inactivity.",
                )
                self.show_login_screen()
                return
            self._session_job = self.root.after(15000, self._check_session_timeout)

    def _on_close(self) -> None:
        self._stop_session_monitor()
        self.db.close()
        self.root.destroy()

    def _clear_root(self) -> None:
        for widget in self.root.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # LOGIN SCREEN (MODULE 1)
    # ------------------------------------------------------------------
    def show_login_screen(self) -> None:
        self._stop_session_monitor()
        self._clear_root()

        wrapper = tk.Frame(self.root, bg=BG_GREY)
        wrapper.pack(fill="both", expand=True)

        card = tk.Frame(
            wrapper, bg=WHITE, bd=1, relief="solid", highlightbackground=BORDER_GREY
        )
        card.place(relx=0.5, rely=0.5, anchor="center", width=420, height=430)

        header = tk.Frame(card, bg=NAVY, height=90)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header, text="Contact Management System", bg=NAVY, fg=WHITE, font=("Segoe UI", 15, "bold")
        ).pack(pady=(22, 2))
        tk.Label(
            header, text="Offline Secure Desktop Application", bg=NAVY, fg="#CBD5E1", font=FONT_SMALL
        ).pack()

        body = tk.Frame(card, bg=WHITE, padx=32, pady=24)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Username", bg=WHITE, fg=TEXT_DARK, font=FONT_BOLD).pack(anchor="w")
        self.login_user_var = tk.StringVar()
        user_entry = ttk.Entry(body, textvariable=self.login_user_var, font=FONT_BODY)
        user_entry.pack(fill="x", pady=(4, 14), ipady=4)
        user_entry.focus_set()

        tk.Label(body, text="Password", bg=WHITE, fg=TEXT_DARK, font=FONT_BOLD).pack(anchor="w")
        self.login_pass_var = tk.StringVar()
        pass_entry = ttk.Entry(body, textvariable=self.login_pass_var, show="*", font=FONT_BODY)
        pass_entry.pack(fill="x", pady=(4, 8), ipady=4)

        show_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            body,
            text="Show Password",
            variable=show_var,
            bg=WHITE,
            fg=TEXT_MUTED,
            activebackground=WHITE,
            font=FONT_SMALL,
            command=lambda: pass_entry.config(show="" if show_var.get() else "*"),
        ).pack(anchor="w", pady=(0, 12))

        self.login_msg_label = tk.Label(
            body, text="", bg=WHITE, fg=DANGER, font=FONT_SMALL, wraplength=350, justify="left"
        )
        self.login_msg_label.pack(anchor="w", pady=(0, 10))

        login_btn = tk.Button(
            body,
            text="Sign In",
            bg=NAVY,
            fg=WHITE,
            activebackground=NAVY_HOVER,
            activeforeground=WHITE,
            font=FONT_BOLD,
            relief="flat",
            cursor="hand2",
            pady=8,
            command=self._handle_login,
        )
        login_btn.pack(fill="x")

        user_entry.bind("<Return>", lambda _e: pass_entry.focus_set())
        pass_entry.bind("<Return>", lambda _e: self._handle_login())

    def _handle_login(self) -> None:
        ok, msg = self.auth.login(self.login_user_var.get(), self.login_pass_var.get())
        if not ok:
            self.login_msg_label.config(text=msg, fg=DANGER)
            return
        self._start_session_monitor()
        self.show_main_layout()

    # ------------------------------------------------------------------
    # MAIN LAYOUT (SIDEBAR + TOPBAR + CONTENT)
    # ------------------------------------------------------------------
    def show_main_layout(self) -> None:
        self._clear_root()

        # Sidebar
        sidebar = tk.Frame(self.root, bg=NAVY, width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="CMS Desktop", bg=NAVY, fg=WHITE, font=("Segoe UI", 16, "bold")
        ).pack(pady=(22, 4), padx=16, anchor="w")
        tk.Label(
            sidebar, text="Contact Manager", bg=NAVY, fg="#94A3B8", font=FONT_SMALL
        ).pack(pady=(0, 20), padx=16, anchor="w")

        nav_items = [
            ("Dashboard", self.show_dashboard),
            ("Contacts", self.show_contacts_view),
            ("Groups", self.show_groups_view),
            ("Import / Export / Backup", self.show_ie_backup_view),
            ("Reports", self.show_reports_view),
        ]
        if self.auth.is_admin():
            nav_items.append(("User Management", self.show_users_view))

        self.nav_buttons = {}
        for label, cmd in nav_items:
            btn = tk.Button(
                sidebar,
                text=f"  {label}",
                bg=NAVY,
                fg=WHITE,
                activebackground=NAVY_HOVER,
                activeforeground=WHITE,
                font=FONT_BODY,
                anchor="w",
                relief="flat",
                padx=14,
                pady=11,
                cursor="hand2",
                command=lambda c=cmd, l=label: self._navigate(l, c),
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[label] = btn

        # Right area
        right_area = tk.Frame(self.root, bg=BG_GREY)
        right_area.pack(side="right", fill="both", expand=True)

        # Top bar
        topbar = tk.Frame(right_area, bg=WHITE, height=56, bd=1, relief="solid")
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        self.page_title_var = tk.StringVar(value="Dashboard")
        tk.Label(
            topbar, textvariable=self.page_title_var, bg=WHITE, fg=NAVY, font=("Segoe UI", 14, "bold")
        ).pack(side="left", padx=20)

        user = self.auth.current_user
        tk.Button(
            topbar,
            text="Logout",
            bg=DANGER,
            fg=WHITE,
            activebackground="#A93226",
            activeforeground=WHITE,
            font=FONT_SMALL,
            relief="flat",
            padx=14,
            pady=5,
            cursor="hand2",
            command=self._handle_logout,
        ).pack(side="right", padx=16)

        tk.Label(
            topbar,
            text=f"{user['username']}  ({user['role']})",
            bg=WHITE,
            fg=TEXT_DARK,
            font=FONT_BOLD,
        ).pack(side="right", padx=8)

        # Content container
        self.content_frame = tk.Frame(right_area, bg=BG_GREY, padx=20, pady=18)
        self.content_frame.pack(fill="both", expand=True)

        self._navigate("Dashboard", self.show_dashboard)

    def _navigate(self, label: str, view_fn) -> None:
        self.page_title_var.set(label)
        for name, btn in self.nav_buttons.items():
            btn.config(bg=NAVY_HOVER if name == label else NAVY)
        for w in self.content_frame.winfo_children():
            w.destroy()
        view_fn()

    def _handle_logout(self) -> None:
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out?"):
            self.auth.logout()
            self.show_login_screen()

    # ------------------------------------------------------------------
    # DASHBOARD VIEW
    # ------------------------------------------------------------------
    def show_dashboard(self) -> None:
        stats = self.contact_mgr.get_dashboard_stats()
        cards_frame = tk.Frame(self.content_frame, bg=BG_GREY)
        cards_frame.pack(fill="x", pady=(0, 18))

        card_specs = [
            ("Total Contacts", stats["total_contacts"], NAVY),
            ("Contact Groups", stats["total_groups"], "#2471A3"),
            ("Added (Last 30 Days)", stats["recent_contacts"], SUCCESS),
            ("Registered Users", stats["total_users"], "#5B2C6F"),
        ]
        for idx, (title, value, accent) in enumerate(card_specs):
            card = tk.Frame(cards_frame, bg=WHITE, bd=1, relief="solid", padx=18, pady=16)
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 10, 0))
            cards_frame.columnconfigure(idx, weight=1)
            tk.Frame(card, bg=accent, height=4).pack(fill="x", pady=(0, 10))
            tk.Label(card, text=title, bg=WHITE, fg=TEXT_MUTED, font=FONT_SMALL).pack(anchor="w")
            tk.Label(card, text=str(value), bg=WHITE, fg=TEXT_DARK, font=("Segoe UI", 24, "bold")).pack(
                anchor="w", pady=(4, 0)
            )

        info_box = tk.Frame(self.content_frame, bg=WHITE, bd=1, relief="solid", padx=20, pady=18)
        info_box.pack(fill="both", expand=True)
        tk.Label(info_box, text="Quick Overview", bg=WHITE, fg=NAVY, font=FONT_HEADING).pack(anchor="w")
        tk.Label(
            info_box,
            text=(
                "Use the sidebar on the left to manage contacts, organize groups, "
                "import/export CSV files, create SQLite backups, and generate reports.\n"
                "All changes are saved locally in contacts.db."
            ),
            bg=WHITE,
            fg=TEXT_MUTED,
            font=FONT_BODY,
            justify="left",
        ).pack(anchor="w", pady=(8, 14))

        btn_row = tk.Frame(info_box, bg=WHITE)
        btn_row.pack(anchor="w")
        self._make_btn(btn_row, "Manage Contacts", lambda: self._navigate("Contacts", self.show_contacts_view)).pack(
            side="left", padx=(0, 10)
        )
        self._make_btn(btn_row, "Generate Reports", lambda: self._navigate("Reports", self.show_reports_view)).pack(
            side="left", padx=(0, 10)
        )
        self._make_btn(
            btn_row, "Backup & CSV", lambda: self._navigate("Import / Export / Backup", self.show_ie_backup_view)
        ).pack(side="left")

    # ------------------------------------------------------------------
    # CONTACTS VIEW (MODULE 3 & MODULE 4)
    # ------------------------------------------------------------------
    def show_contacts_view(self) -> None:
        self.selected_contact_id: int | None = None

        # Search & Filter Bar
        search_bar = tk.Frame(self.content_frame, bg=WHITE, bd=1, relief="solid", padx=12, pady=10)
        search_bar.pack(fill="x", pady=(0, 12))

        tk.Label(search_bar, text="Search:", bg=WHITE, fg=TEXT_DARK, font=FONT_BOLD).pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_bar, textvariable=self.search_var, width=30, font=FONT_BODY)
        search_entry.pack(side="left", padx=(6, 14))

        tk.Label(search_bar, text="Group:", bg=WHITE, fg=TEXT_DARK, font=FONT_BOLD).pack(side="left")
        groups = self.group_mgr.list_groups()
        self.filter_group_map = {"All Groups": None}
        for g in groups:
            self.filter_group_map[g[1]] = g[0]

        self.filter_group_var = tk.StringVar(value="All Groups")
        filter_combo = ttk.Combobox(
            search_bar,
            textvariable=self.filter_group_var,
            values=list(self.filter_group_map.keys()),
            state="readonly",
            width=18,
        )
        filter_combo.pack(side="left", padx=(6, 12))

        self._make_btn(search_bar, "Search", self._refresh_contacts_table).pack(side="left", padx=(0, 6))
        self._make_btn(search_bar, "Reset", self._reset_contact_search, bg="#64748B").pack(side="left")

        search_entry.bind("<KeyRelease>", lambda _e: self._refresh_contacts_table())
        filter_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_contacts_table())

        # Main split: Form (left) + Table (right)
        body = tk.Frame(self.content_frame, bg=BG_GREY)
        body.pack(fill="both", expand=True)

        form = tk.Frame(body, bg=WHITE, bd=1, relief="solid", padx=14, pady=14, width=310)
        form.pack(side="left", fill="y", padx=(0, 12))
        form.pack_propagate(False)

        tk.Label(form, text="Contact Details", bg=WHITE, fg=NAVY, font=FONT_HEADING).pack(anchor="w", pady=(0, 10))

        self.c_first = tk.StringVar()
        self.c_last = tk.StringVar()
        self.c_phone = tk.StringVar()
        self.c_email = tk.StringVar()
        self.c_address = tk.StringVar()
        self.c_group = tk.StringVar(value="General")

        for lbl, var in [
            ("First Name *", self.c_first),
            ("Last Name", self.c_last),
            ("Phone (10 digits) *", self.c_phone),
            ("Email", self.c_email),
            ("Address", self.c_address),
        ]:
            tk.Label(form, text=lbl, bg=WHITE, fg=TEXT_DARK, font=FONT_SMALL).pack(anchor="w")
            ttk.Entry(form, textvariable=var, font=FONT_BODY).pack(fill="x", pady=(2, 8))

        tk.Label(form, text="Group", bg=WHITE, fg=TEXT_DARK, font=FONT_SMALL).pack(anchor="w")
        self.form_group_map = {g[1]: g[0] for g in groups}
        ttk.Combobox(
            form,
            textvariable=self.c_group,
            values=list(self.form_group_map.keys()),
            state="readonly",
        ).pack(fill="x", pady=(2, 14))

        btn_grid = tk.Frame(form, bg=WHITE)
        btn_grid.pack(fill="x")
        self._make_btn(btn_grid, "Add", self._add_contact, bg=SUCCESS).grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=3)
        self._make_btn(btn_grid, "Update", self._update_contact).grid(row=0, column=1, sticky="ew", padx=(4, 0), pady=3)
        self._make_btn(btn_grid, "Delete", self._delete_contact, bg=DANGER).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=3)
        self._make_btn(btn_grid, "Clear", self._clear_contact_form, bg="#64748B").grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=3)
        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

        # Table
        table_box = tk.Frame(body, bg=WHITE, bd=1, relief="solid", padx=10, pady=10)
        table_box.pack(side="right", fill="both", expand=True)

        cols = ("ID", "First Name", "Last Name", "Phone", "Email", "Address", "Group", "Created On")
        self.contacts_tree = ttk.Treeview(table_box, columns=cols, show="headings", selectmode="extended")
        widths = (45, 110, 100, 105, 160, 150, 95, 95)
        for col, w in zip(cols, widths):
            self.contacts_tree.heading(col, text=col)
            self.contacts_tree.column(col, width=w, anchor="w")

        vsb = ttk.Scrollbar(table_box, orient="vertical", command=self.contacts_tree.yview)
        hsb = ttk.Scrollbar(table_box, orient="horizontal", command=self.contacts_tree.xview)
        self.contacts_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.contacts_tree.pack(side="top", fill="both", expand=True)
        vsb.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")
        hsb.pack(side="bottom", fill="x")

        self.contacts_status = tk.Label(table_box, text="", bg=WHITE, fg=TEXT_MUTED, font=FONT_SMALL)
        self.contacts_status.pack(anchor="w", pady=(6, 0))

        self.contacts_tree.bind("<<TreeviewSelect>>", self._on_contact_select)
        self._refresh_contacts_table()

    def _refresh_contacts_table(self) -> None:
        for item in self.contacts_tree.get_children():
            self.contacts_tree.delete(item)
        gid = self.filter_group_map.get(self.filter_group_var.get())
        rows = self.contact_mgr.search_contacts(self.search_var.get(), gid)
        for r in rows:
            self.contacts_tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[8]))
        if not rows:
            self.contacts_status.config(text="No matching contacts found.")
        else:
            self.contacts_status.config(text=f"Showing {len(rows)} contact(s).")

    def _reset_contact_search(self) -> None:
        self.search_var.set("")
        self.filter_group_var.set("All Groups")
        self._refresh_contacts_table()

    def _on_contact_select(self, _event) -> None:
        sel = self.contacts_tree.selection()
        if not sel:
            return
        vals = self.contacts_tree.item(sel[0], "values")
        self.selected_contact_id = int(vals[0])
        self.c_first.set(vals[1])
        self.c_last.set(vals[2])
        self.c_phone.set(vals[3])
        self.c_email.set(vals[4])
        self.c_address.set(vals[5])
        self.c_group.set(vals[6])

    def _clear_contact_form(self) -> None:
        self.selected_contact_id = None
        for var in (self.c_first, self.c_last, self.c_phone, self.c_email, self.c_address):
            var.set("")
        self.c_group.set("General")

    def _add_contact(self) -> None:
        gid = self.form_group_map.get(self.c_group.get())
        ok, msg = self.contact_mgr.add_contact(
            self.c_first.get(),
            self.c_last.get(),
            self.c_phone.get(),
            self.c_email.get(),
            self.c_address.get(),
            gid,
            self.auth.current_user["user_id"],
        )
        if ok:
            messagebox.showinfo("Success", msg)
            self._clear_contact_form()
            self._refresh_contacts_table()
        else:
            messagebox.showerror("Validation Error", msg)

    def _update_contact(self) -> None:
        if self.selected_contact_id is None:
            messagebox.showwarning("Select Contact", "Please select a contact from the table to update.")
            return
        gid = self.form_group_map.get(self.c_group.get())
        ok, msg = self.contact_mgr.update_contact(
            self.selected_contact_id,
            self.c_first.get(),
            self.c_last.get(),
            self.c_phone.get(),
            self.c_email.get(),
            self.c_address.get(),
            gid,
        )
        if ok:
            messagebox.showinfo("Success", msg)
            self._clear_contact_form()
            self._refresh_contacts_table()
        else:
            messagebox.showerror("Validation Error", msg)

    def _delete_contact(self) -> None:
        if self.selected_contact_id is None:
            messagebox.showwarning("Select Contact", "Please select a contact from the table to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected contact?"):
            return
        ok, msg = self.contact_mgr.delete_contact(self.selected_contact_id)
        if ok:
            messagebox.showinfo("Deleted", msg)
            self._clear_contact_form()
            self._refresh_contacts_table()
        else:
            messagebox.showerror("Error", msg)

    # ------------------------------------------------------------------
    # GROUPS VIEW (MODULE 2)
    # ------------------------------------------------------------------
    def show_groups_view(self) -> None:
        self.selected_group_id: int | None = None

        top = tk.Frame(self.content_frame, bg=WHITE, bd=1, relief="solid", padx=16, pady=14)
        top.pack(fill="x", pady=(0, 12))

        tk.Label(top, text="Group Name *", bg=WHITE, fg=TEXT_DARK, font=FONT_BOLD).grid(row=0, column=0, sticky="w")
        self.g_name = tk.StringVar()
        ttk.Entry(top, textvariable=self.g_name, width=25).grid(row=0, column=1, padx=(8, 16))

        tk.Label(top, text="Description", bg=WHITE, fg=TEXT_DARK, font=FONT_BOLD).grid(row=0, column=2, sticky="w")
        self.g_desc = tk.StringVar()
        ttk.Entry(top, textvariable=self.g_desc, width=35).grid(row=0, column=3, padx=(8, 16))

        self._make_btn(top, "Add Group", self._add_group, bg=SUCCESS).grid(row=0, column=4, padx=4)
        self._make_btn(top, "Rename / Save", self._edit_group).grid(row=0, column=5, padx=4)
        if self.auth.is_admin():
            self._make_btn(top, "Delete Group", self._delete_group, bg=DANGER).grid(row=0, column=6, padx=4)

        table_box = tk.Frame(self.content_frame, bg=WHITE, bd=1, relief="solid", padx=12, pady=12)
        table_box.pack(fill="both", expand=True)

        cols = ("ID", "Group Name", "Description", "Total Contacts")
        self.groups_tree = ttk.Treeview(table_box, columns=cols, show="headings")
        for col, w in zip(cols, (60, 220, 420, 130)):
            self.groups_tree.heading(col, text=col)
            self.groups_tree.column(col, width=w, anchor="w")
        self.groups_tree.pack(fill="both", expand=True)
        self.groups_tree.bind("<<TreeviewSelect>>", self._on_group_select)
        self._refresh_groups_table()

    def _refresh_groups_table(self) -> None:
        for item in self.groups_tree.get_children():
            self.groups_tree.delete(item)
        for row in self.group_mgr.list_groups():
            self.groups_tree.insert("", "end", values=row)

    def _on_group_select(self, _event) -> None:
        sel = self.groups_tree.selection()
        if not sel:
            return
        vals = self.groups_tree.item(sel[0], "values")
        self.selected_group_id = int(vals[0])
        self.g_name.set(vals[1])
        self.g_desc.set(vals[2])

    def _add_group(self) -> None:
        ok, msg = self.group_mgr.add_group(self.g_name.get(), self.g_desc.get())
        if ok:
            messagebox.showinfo("Success", msg)
            self.g_name.set("")
            self.g_desc.set("")
            self._refresh_groups_table()
        else:
            messagebox.showerror("Error", msg)

    def _edit_group(self) -> None:
        if self.selected_group_id is None:
            messagebox.showwarning("Select Group", "Please select a group to rename or update.")
            return
        ok, msg = self.group_mgr.edit_group(self.selected_group_id, self.g_name.get(), self.g_desc.get())
        if ok:
            messagebox.showinfo("Success", msg)
            self._refresh_groups_table()
        else:
            messagebox.showerror("Error", msg)

    def _delete_group(self) -> None:
        if self.selected_group_id is None:
            messagebox.showwarning("Select Group", "Please select a group to delete.")
            return
        if not messagebox.askyesno(
            "Confirm Delete",
            "Delete this group? All its contacts will be moved automatically to 'General'.",
        ):
            return
        try:
            ok, msg = self.group_mgr.delete_group(self.selected_group_id, self.auth.current_user["role"])
            if ok:
                messagebox.showinfo("Deleted", msg)
                self.selected_group_id = None
                self.g_name.set("")
                self.g_desc.set("")
                self._refresh_groups_table()
            else:
                messagebox.showerror("Error", msg)
        except PermissionError as exc:
            messagebox.showerror("Access Denied", str(exc))

    # ------------------------------------------------------------------
    # IMPORT / EXPORT / BACKUP VIEW (MODULE 5)
    # ------------------------------------------------------------------
    def show_ie_backup_view(self) -> None:
        actions = tk.Frame(self.content_frame, bg=WHITE, bd=1, relief="solid", padx=16, pady=16)
        actions.pack(fill="x", pady=(0, 14))

        tk.Label(actions, text="CSV Import / Export & Database Backup", bg=WHITE, fg=NAVY, font=FONT_HEADING).pack(
            anchor="w", pady=(0, 12)
        )

        btn_row = tk.Frame(actions, bg=WHITE)
        btn_row.pack(anchor="w")
        self._make_btn(btn_row, "Import Contacts (CSV)", self._import_csv, bg=SUCCESS).pack(side="left", padx=(0, 10))
        self._make_btn(btn_row, "Export All Contacts (CSV)", self._export_csv).pack(side="left", padx=(0, 10))
        self._make_btn(btn_row, "Create Database Backup", self._create_backup, bg="#2471A3").pack(side="left", padx=(0, 10))
        if self.auth.is_admin():
            self._make_btn(btn_row, "Restore Database (Admin)", self._restore_backup, bg=DANGER).pack(side="left")

        hist_box = tk.Frame(self.content_frame, bg=WHITE, bd=1, relief="solid", padx=14, pady=14)
        hist_box.pack(fill="both", expand=True)

        tk.Label(hist_box, text="Backup History", bg=WHITE, fg=NAVY, font=FONT_HEADING).pack(anchor="w", pady=(0, 8))
        cols = ("Backup ID", "Backup Date", "Backup Filename", "Performed By")
        self.backup_tree = ttk.Treeview(hist_box, columns=cols, show="headings")
        for col, w in zip(cols, (90, 200, 340, 160)):
            self.backup_tree.heading(col, text=col)
            self.backup_tree.column(col, width=w, anchor="w")
        self.backup_tree.pack(fill="both", expand=True)
        self._refresh_backup_history()

    def _refresh_backup_history(self) -> None:
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        for row in self.backup_mgr.get_backup_history():
            self.backup_tree.insert("", "end", values=row)

    def _import_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="Select CSV File to Import", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not path:
            return
        try:
            s = self.ie_mgr.import_contacts_csv(path, self.auth.current_user["user_id"])
            messagebox.showinfo(
                "CSV Import Summary",
                f"Total records processed: {s['total']}\n"
                f"Successfully imported: {s['imported']}\n"
                f"Skipped duplicates: {s['duplicates']}\n"
                f"Invalid records: {s['invalid']}",
            )
        except Exception as exc:
            messagebox.showerror("Import Failed", str(exc))

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export Contacts to CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not path:
            return
        try:
            count = self.ie_mgr.export_contacts_csv(path)
            messagebox.showinfo("Export Complete", f"Successfully exported {count} contact(s) to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Export Failed", str(exc))

    def _create_backup(self) -> None:
        ok, res = self.backup_mgr.create_backup(self.auth.current_user["user_id"])
        if ok:
            messagebox.showinfo("Backup Created", f"Database backup saved to:\n{res}")
            self._refresh_backup_history()
        else:
            messagebox.showerror("Backup Error", res)

    def _restore_backup(self) -> None:
        path = filedialog.askopenfilename(
            title="Select SQLite Backup File", filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")]
        )
        if not path:
            return
        if not messagebox.askyesno(
            "Confirm Restore",
            "Restoring a backup will replace the current database. Continue?",
        ):
            return
        try:
            ok, msg = self.backup_mgr.restore_backup(path, self.auth.current_user["role"])
            if ok:
                messagebox.showinfo("Restored", msg)
                self._refresh_backup_history()
            else:
                messagebox.showerror("Restore Failed", msg)
        except PermissionError as exc:
            messagebox.showerror("Access Denied", str(exc))

    # ------------------------------------------------------------------
    # REPORTS VIEW (MODULE 6)
    # ------------------------------------------------------------------
    def show_reports_view(self) -> None:
        bar = tk.Frame(self.content_frame, bg=WHITE, bd=1, relief="solid", padx=14, pady=12)
        bar.pack(fill="x", pady=(0, 12))

        report_options = [
            "1. All Contacts List (Alphabetical)",
            "2. Group-wise Contact List",
            "3. Incomplete Contacts (Missing Email or Address)",
            "4. Recently Added Contacts (Last 30 Days)",
            "5. Possible Duplicate Contacts",
            "6. Backup History Report",
        ]
        if self.auth.is_admin():
            report_options.append("7. User List (Admin Only)")

        tk.Label(bar, text="Report:", bg=WHITE, fg=TEXT_DARK, font=FONT_BOLD).pack(side="left")
        self.report_type_var = tk.StringVar(value=report_options[0])
        ttk.Combobox(
            bar, textvariable=self.report_type_var, values=report_options, state="readonly", width=40
        ).pack(side="left", padx=(6, 12))

        groups = self.group_mgr.list_groups()
        self.rep_group_map = {"All Groups": None}
        for g in groups:
            self.rep_group_map[g[1]] = g[0]
        self.rep_group_var = tk.StringVar(value="All Groups")
        ttk.Combobox(
            bar, textvariable=self.rep_group_var, values=list(self.rep_group_map.keys()), state="readonly", width=16
        ).pack(side="left", padx=(0, 12))

        self._make_btn(bar, "Generate", self._generate_report).pack(side="left", padx=(0, 6))
        self._make_btn(bar, "Export CSV", self._export_report_csv, bg=SUCCESS).pack(side="left", padx=(0, 6))
        self._make_btn(bar, "Print", self._print_report, bg="#2471A3").pack(side="left")

        self.report_table_frame = tk.Frame(self.content_frame, bg=WHITE, bd=1, relief="solid", padx=12, pady=12)
        self.report_table_frame.pack(fill="both", expand=True)
        self._generate_report()

    def _generate_report(self) -> None:
        choice = self.report_type_var.get()
        if choice.startswith("1."):
            headers, rows = self.report_gen.all_contacts()
        elif choice.startswith("2."):
            gid = self.rep_group_map.get(self.rep_group_var.get())
            headers, rows = self.report_gen.group_wise(gid)
        elif choice.startswith("3."):
            headers, rows = self.report_gen.incomplete_contacts()
        elif choice.startswith("4."):
            headers, rows = self.report_gen.recently_added(30)
        elif choice.startswith("5."):
            headers, rows = self.report_gen.possible_duplicates()
        elif choice.startswith("6."):
            headers, rows = self.report_gen.backup_history()
        else:
            headers, rows = self.report_gen.user_list(self.auth.current_user["role"])

        self._current_report_data = (choice, headers, rows)

        for w in self.report_table_frame.winfo_children():
            w.destroy()

        tree = ttk.Treeview(self.report_table_frame, columns=headers, show="headings")
        for h in headers:
            tree.heading(h, text=h)
            tree.column(h, width=130, anchor="w")
        for r in rows:
            tree.insert("", "end", values=r)
        tree.pack(fill="both", expand=True)

        tk.Label(
            self.report_table_frame,
            text=f"Total rows: {len(rows)}",
            bg=WHITE,
            fg=TEXT_MUTED,
            font=FONT_SMALL,
        ).pack(anchor="w", pady=(6, 0))

    def _export_report_csv(self) -> None:
        title, headers, rows = self._current_report_data
        if not headers:
            return
        path = filedialog.asksaveasfilename(
            title="Export Report to CSV", defaultextension=".csv", filetypes=[("CSV Files", "*.csv")]
        )
        if not path:
            return
        self.report_gen.export_csv(path, headers, rows)
        messagebox.showinfo("Exported", f"Report '{title}' exported to:\n{path}")

    def _print_report(self) -> None:
        title, headers, rows = self._current_report_data
        if not headers:
            return
        ok, msg = self.report_gen.print_report(title, headers, rows)
        if ok:
            messagebox.showinfo("Print", msg)
        else:
            messagebox.showwarning("Print Info", msg)

    # ------------------------------------------------------------------
    # USER MANAGEMENT VIEW (MODULE 1 - ADMIN ONLY)
    # ------------------------------------------------------------------
    def show_users_view(self) -> None:
        self.selected_user_id: int | None = None

        form = tk.Frame(self.content_frame, bg=WHITE, bd=1, relief="solid", padx=14, pady=12)
        form.pack(fill="x", pady=(0, 12))

        tk.Label(form, text="Username", bg=WHITE, fg=TEXT_DARK, font=FONT_BOLD).grid(row=0, column=0, sticky="w")
        self.u_name = tk.StringVar()
        ttk.Entry(form, textvariable=self.u_name, width=20).grid(row=0, column=1, padx=(6, 12))

        tk.Label(form, text="Password", bg=WHITE, fg=TEXT_DARK, font=FONT_BOLD).grid(row=0, column=2, sticky="w")
        self.u_pass = tk.StringVar()
        ttk.Entry(form, textvariable=self.u_pass, show="*", width=20).grid(row=0, column=3, padx=(6, 12))

        tk.Label(form, text="Role", bg=WHITE, fg=TEXT_DARK, font=FONT_BOLD).grid(row=0, column=4, sticky="w")
        self.u_role = tk.StringVar(value="User")
        ttk.Combobox(form, textvariable=self.u_role, values=("Admin", "User"), state="readonly", width=10).grid(
            row=0, column=5, padx=(6, 12)
        )

        self._make_btn(form, "Create", self._create_user, bg=SUCCESS).grid(row=0, column=6, padx=3)
        self._make_btn(form, "Update", self._edit_user).grid(row=0, column=7, padx=3)
        self._make_btn(form, "Reset Password", self._reset_user_pwd, bg="#2471A3").grid(row=0, column=8, padx=3)
        self._make_btn(form, "Delete", self._delete_user, bg=DANGER).grid(row=0, column=9, padx=3)

        table_box = tk.Frame(self.content_frame, bg=WHITE, bd=1, relief="solid", padx=12, pady=12)
        table_box.pack(fill="both", expand=True)

        cols = ("User ID", "Username", "Role", "Created On")
        self.users_tree = ttk.Treeview(table_box, columns=cols, show="headings")
        for col, w in zip(cols, (90, 220, 140, 160)):
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=w, anchor="w")
        self.users_tree.pack(fill="both", expand=True)
        self.users_tree.bind("<<TreeviewSelect>>", self._on_user_select)
        self._refresh_users_table()

    def _refresh_users_table(self) -> None:
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        for row in self.user_mgr.list_users():
            self.users_tree.insert("", "end", values=row)

    def _on_user_select(self, _event) -> None:
        sel = self.users_tree.selection()
        if not sel:
            return
        vals = self.users_tree.item(sel[0], "values")
        self.selected_user_id = int(vals[0])
        self.u_name.set(vals[1])
        self.u_role.set(vals[2])
        self.u_pass.set("")

    def _create_user(self) -> None:
        ok, msg = self.user_mgr.create_user(
            self.u_name.get(), self.u_pass.get(), self.u_role.get(), self.auth.current_user["role"]
        )
        if ok:
            messagebox.showinfo("Success", msg)
            self.u_name.set("")
            self.u_pass.set("")
            self._refresh_users_table()
        else:
            messagebox.showerror("Error", msg)

    def _edit_user(self) -> None:
        if self.selected_user_id is None:
            messagebox.showwarning("Select User", "Please select a user to update.")
            return
        ok, msg = self.user_mgr.edit_user(
            self.selected_user_id, self.u_name.get(), self.u_role.get(), self.auth.current_user["role"]
        )
        if ok:
            messagebox.showinfo("Success", msg)
            self._refresh_users_table()
        else:
            messagebox.showerror("Error", msg)

    def _reset_user_pwd(self) -> None:
        if self.selected_user_id is None:
            messagebox.showwarning("Select User", "Please select a user to reset password.")
            return
        new_pwd = simpledialog.askstring("Reset Password", "Enter new password (min 6 chars):", show="*")
        if not new_pwd:
            return
        ok, msg = self.user_mgr.reset_password(self.selected_user_id, new_pwd, self.auth.current_user["role"])
        if ok:
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)

    def _delete_user(self) -> None:
        if self.selected_user_id is None:
            messagebox.showwarning("Select User", "Please select a user to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this user?"):
            return
        ok, msg = self.user_mgr.delete_user(
            self.selected_user_id, self.auth.current_user["user_id"], self.auth.current_user["role"]
        )
        if ok:
            messagebox.showinfo("Deleted", msg)
            self.selected_user_id = None
            self._refresh_users_table()
        else:
            messagebox.showerror("Error", msg)

    # ------------------------------------------------------------------
    # UI HELPER
    # ------------------------------------------------------------------
    @staticmethod
    def _make_btn(parent, text: str, command, bg: str = NAVY) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            bg=bg,
            fg=WHITE,
            activebackground=NAVY_HOVER,
            activeforeground=WHITE,
            font=FONT_SMALL,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
            command=command,
        )
