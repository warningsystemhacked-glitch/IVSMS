"""
Integrated Vehicle Service Management System (IVSMS)
GUI: Tkinter | Database: SQLite | Concepts: OOP, CRUD, validation, login

Modules:
  Customer, Vehicle, Service, Parts, Mechanic, Payment Records,
  Service History, Reports  + Login / Logout

Default login:  admin / ivsms12345
Run:            python ivsms.py
"""
import csv
import sqlite3
import hashlib
from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font as tkfont

STATUSES = ["Pending", "In Progress", "Completed"]
PAY_METHODS = ["Cash", "GCash", "Card"]
LOW_STOCK = 5

# ----------------------------------------------------------------- THEME
INK = "#1F2933"          
INK_SOFT = "#323F4B"
ACCENT = "#D9480F"      
ACCENT_DARK = "#BF3F0A"
ACCENT_SOFT = "#FFE8D9"  
BG = "#F1F3F5"
CARD = "#FFFFFF"
BORDER = "#DEE2E6"
MUTED = "#6B7280"
ZEBRA = "#F8F9FA"
DANGER = "#C92A2A"
STATUS_COLORS = {"Pending": "#946200", "InProgress": "#1971C2", "Completed": "#2B8A3E"}

FONT = "Segoe UI"  


def f(size=10, bold=False):
    return (FONT, size, "bold") if bold else (FONT, size)


def apply_theme(root):
    """One place for all colours / fonts, so every screen looks consistent."""
    global FONT
    available = set(tkfont.families(root))
    for name in ("Segoe UI", "Helvetica Neue", "Ubuntu", "DejaVu Sans", "Arial"):
        if name in available:
            FONT = name
            break

    root.configure(bg=BG)
    root.option_add("*TCombobox*Listbox.font", f(10))
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TButton.cursor", "hand2")

    s = ttk.Style(root)
    s.theme_use("clam")

    # frames & labels
    s.configure("TFrame", background=BG)
    s.configure("Card.TFrame", background=CARD)
    s.configure("TLabel", background=BG, foreground=INK, font=f(10))
    s.configure("Card.TLabel", background=CARD)
    s.configure("Title.TLabel", font=f(18, True))
    s.configure("Muted.TLabel", foreground=MUTED)
    s.configure("CardMuted.TLabel", background=CARD, foreground=MUTED)
    s.configure("Card.TLabelframe", background=CARD, bordercolor=BORDER,
                borderwidth=1, relief="solid")
    s.configure("Card.TLabelframe.Label", background=CARD, foreground=ACCENT,
                font=f(10, True))

    # inputs
    for widget in ("TEntry", "TCombobox"):
        s.configure(widget, fieldbackground=CARD, foreground=INK, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, padding=6)
        s.map(widget, bordercolor=[("focus", ACCENT)], lightcolor=[("focus", ACCENT)],
              darkcolor=[("focus", ACCENT)])
    s.map("TCombobox", fieldbackground=[("readonly", CARD)],
          selectbackground=[("readonly", CARD)], selectforeground=[("readonly", INK)])

    # buttons
    s.configure("TButton", font=f(10), padding=(14, 7), relief="flat", borderwidth=0,
                background="#E9ECEF", foreground=INK, focuscolor="#E9ECEF")
    s.map("TButton", background=[("pressed", "#CED4DA"), ("active", "#DEE2E6")])
    for name, bg, hover, fg in [
        ("Accent.TButton", ACCENT, ACCENT_DARK, "white"),
        ("Danger.TButton", DANGER, "#A61E1E", "white"),
        ("Soft.TButton", ACCENT_SOFT, "#FFD8BF", "#9C3208"),
        ("Top.TButton", INK_SOFT, "#3E4C59", "white"),
    ]:
        s.configure(name, background=bg, foreground=fg, focuscolor=bg,
                    font=f(10, True))
        s.map(name, background=[("pressed", hover), ("active", hover)])

    # tables
    s.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=INK,
                rowheight=30, borderwidth=0, font=f(10))
    s.map("Treeview", background=[("selected", ACCENT_SOFT)],
          foreground=[("selected", INK)])
    s.configure("Treeview.Heading", background="#E9ECEF", foreground=INK,
                font=f(10, True), relief="flat", padding=(8, 7))
    s.map("Treeview.Heading", background=[("active", "#DEE2E6")])
    s.configure("Vertical.TScrollbar", background="#CED4DA", troughcolor=BG,
                bordercolor=BG, arrowcolor=MUTED, relief="flat")

    # tabs
    s.configure("TNotebook", background=BG, borderwidth=0, tabmargins=(12, 8, 12, 0))
    s.configure("TNotebook.Tab", padding=(16, 9), background="#E1E5E9",
                foreground=MUTED, font=f(10), borderwidth=0)
    s.map("TNotebook.Tab", background=[("selected", BG)],
          foreground=[("selected", ACCENT)], font=[("selected", f(10, True))])


def build_table(parent, columns, height=14):
    """Treeview + scrollbar + zebra rows + coloured status text."""
    wrap = ttk.Frame(parent)
    wrap.pack(fill="both", expand=True)
    tree = ttk.Treeview(wrap, columns=columns, show="headings", height=height)
    bar = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=bar.set)
    tree.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")
    tree.tag_configure("even", background=CARD)
    tree.tag_configure("odd", background=ZEBRA)
    for tag, color in STATUS_COLORS.items():
        tree.tag_configure(tag, foreground=color)
    return tree


def fill_table(tree, rows):
    tree.delete(*tree.get_children())
    for i, row in enumerate(rows):
        tags = ["odd" if i % 2 else "even"]
        for value in row:
            if value in STATUSES:
                tags.append(value.replace(" ", ""))
                break
        tree.insert("", "end", values=tuple(row), tags=tags)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def export_csv(headers, rows):
    """Shared by Service History and Reports."""
    if not rows:
        messagebox.showinfo("Export", "Nothing to export.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv",
                                        filetypes=[("CSV file", "*.csv")])
    if not path:
        return
    try:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(headers)
            writer.writerows(rows)
        messagebox.showinfo("Export", f"Saved {len(rows)} rows.")
    except OSError as e:
        messagebox.showerror("Export failed", str(e))


# ---------------------------------------------------------------- MODELS
class Record:
    """Base class for all records (abstraction + inheritance)."""

    table = ""
    columns = []

    def __init__(self, record_id=None, **data):
        self.id = record_id
        self.data = {c: data.get(c, "") for c in self.columns}
        self.validate()

    def validate(self):  
        raise NotImplementedError

    def values(self):
        return [self.data[c] for c in self.columns]

    def _require(self, col, label):
        self.data[col] = str(self.data[col]).strip()
        if not self.data[col]:
            raise ValueError(f"{label} is required.")

    def _number(self, col, label, cast):
        try:
            self.data[col] = cast(self.data[col])
        except (TypeError, ValueError):
            raise ValueError(f"{label} must be a valid number.")

    def _phone(self):
        self._require("phone", "Phone number")
        if not self.data["phone"].replace("+", "").replace("-", "").isdigit():
            raise ValueError("Phone number must contain digits only.")

    def _date(self):
        try:
            date.fromisoformat(self.data["date"])
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format.")


class Customer(Record):
    table = "customers"
    columns = ["name", "phone"]

    def validate(self):
        self._require("name", "Customer name")
        self._phone()


class Vehicle(Record):
    table = "vehicles"
    columns = ["customer_id", "plate", "model", "year"]

    def validate(self):
        self._require("customer_id", "Owner")
        self._require("plate", "Plate number")
        self._require("model", "Make / Model")
        self._number("customer_id", "Owner", int)
        self._number("year", "Year", int)
        self.data["plate"] = self.data["plate"].upper()
        if not 1950 <= self.data["year"] <= date.today().year + 1:
            raise ValueError("Please enter a valid year.")


class Mechanic(Record):
    table = "mechanics"
    columns = ["name", "phone", "specialty"]

    def validate(self):
        self._require("name", "Mechanic name")
        self._phone()
        self.data["specialty"] = str(self.data["specialty"]).strip()


class Part(Record):
    table = "parts"
    columns = ["name", "price", "stock"]

    def validate(self):
        self._require("name", "Part name")
        self._number("price", "Price", float)
        self._number("stock", "Stock quantity", int)
        if self.data["price"] < 0 or self.data["stock"] < 0:
            raise ValueError("Price and stock cannot be negative.")


class ServiceOrder(Record):
    table = "services"
    columns = ["vehicle_id", "mechanic_id", "description", "cost", "status", "date"]

    def validate(self):
        self._require("vehicle_id", "Vehicle")
        self._require("description", "Service description")
        self._number("vehicle_id", "Vehicle", int)
        self._number("cost", "Cost", float)
        try:  # mechanic is optional: 0 / blank means "not assigned yet"
            self.data["mechanic_id"] = int(self.data["mechanic_id"] or 0) or None
        except ValueError:
            raise ValueError("Invalid mechanic.")
        if self.data["cost"] < 0:
            raise ValueError("Cost cannot be negative.")
        if self.data["status"] not in STATUSES:
            raise ValueError("Please choose a status.")
        self._date()


class Payment(Record):
    table = "payments"
    columns = ["service_id", "amount", "method", "date"]

    def validate(self):
        self._require("service_id", "Service")
        self._number("service_id", "Service", int)
        self._number("amount", "Amount", float)
        if self.data["amount"] <= 0:
            raise ValueError("Amount must be greater than zero.")
        if self.data["method"] not in PAY_METHODS:
            raise ValueError("Please choose a payment method.")
        self._date()


# -------------------------------------------------------------- DATABASE
class Database:
    """All SQL lives here, so the GUI never writes queries for CRUD."""

    def __init__(self, path="ivsms.db"):
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                plate TEXT UNIQUE NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS mechanics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                specialty TEXT);
            CREATE TABLE IF NOT EXISTS parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
                mechanic_id INTEGER REFERENCES mechanics(id),
                description TEXT NOT NULL,
                cost REAL NOT NULL,
                status TEXT NOT NULL,
                date TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER NOT NULL REFERENCES services(id),
                amount REAL NOT NULL,
                method TEXT NOT NULL,
                date TEXT NOT NULL);
            """
        )
        cols = [r[1] for r in self.query("PRAGMA table_info(services)")]
        if "mechanic_id" not in cols:
            self.conn.execute(
                "ALTER TABLE services ADD COLUMN mechanic_id INTEGER REFERENCES mechanics(id)")
        self.conn.execute(
          """INSERT INTO users (username, password) VALUES (?, ?)
           ON CONFLICT(username) DO UPDATE SET password = excluded.password""",
          ("admin", hash_password("ivsms12345")),
        )
        self.conn.commit()

    def query(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def query_with_headers(self, sql):
        cur = self.conn.execute(sql)
        return [d[0] for d in cur.description], cur.fetchall()

    def execute(self, sql, params=()):
        self.conn.execute(sql, params)
        self.conn.commit()

    def check_login(self, username, password):
        return bool(self.query(
            "SELECT id FROM users WHERE username=? AND password=?",
            (username, hash_password(password))))

    def insert(self, rec: Record):
        cols = ", ".join(rec.columns)
        marks = ", ".join("?" * len(rec.columns))
        self.execute(f"INSERT INTO {rec.table} ({cols}) VALUES ({marks})", rec.values())

    def update(self, rec: Record):
        sets = ", ".join(f"{c}=?" for c in rec.columns)
        self.execute(f"UPDATE {rec.table} SET {sets} WHERE id=?", rec.values() + [rec.id])

    def delete(self, table, record_id):
        self.execute(f"DELETE FROM {table} WHERE id=?", (record_id,))


# SQL shared by several screens
SERVICE_JOIN = """FROM services s JOIN vehicles v ON v.id = s.vehicle_id
                  JOIN customers c ON c.id = v.customer_id
                  LEFT JOIN mechanics m ON m.id = s.mechanic_id"""


# ------------------------------------------------------------------- GUI
class BaseWindow(tk.Tk):
    def __init__(self, title, width, height):
        super().__init__()
        self.title(title)
        apply_theme(self)
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.build_ui()

    def build_ui(self):
        raise NotImplementedError


class LoginWindow(BaseWindow):
    def __init__(self, db):
        self.db = db
        super().__init__("IVSMS - Login", 700, 400)

    def build_ui(self):
        self.resizable(False, False)

        # left brand panel
        left = tk.Frame(self, bg=INK, width=280)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        tk.Frame(left, bg=ACCENT, height=6).pack(fill="x")
        tk.Label(left, text="IVSMS", font=f(32, True), fg=ACCENT, bg=INK).pack(pady=(110, 6))
        tk.Label(left, text="Integrated Vehicle\nService Management System",
                 font=f(10), fg="#CBD2D9", bg=INK, justify="center").pack()

        # right form
        right = ttk.Frame(self, style="Card.TFrame", padding=(44, 50))
        right.pack(side="right", fill="both", expand=True)
        ttk.Label(right, text="Welcome back", font=f(18, True),
                  style="Card.TLabel").pack(anchor="w")
        ttk.Label(right, text="Sign in to manage your shop.",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(2, 20))
        ttk.Label(right, text="Username", style="Card.TLabel").pack(anchor="w")
        self.username = ttk.Entry(right)
        self.username.pack(fill="x", pady=(2, 12))
        ttk.Label(right, text="Password", style="Card.TLabel").pack(anchor="w")
        self.password = ttk.Entry(right, show="*")
        self.password.pack(fill="x", pady=(2, 0))
        ttk.Button(right, text="Sign in", style="Accent.TButton",
                   command=self.login).pack(fill="x", pady=(24, 0))
        self.bind("<Return>", lambda e: self.login())
        self.username.focus()

    def login(self):
        if self.db.check_login(self.username.get().strip(), self.password.get()):
            self.destroy()
            MainWindow(self.db).mainloop()
        else:  
            messagebox.showerror("Login failed", "Invalid username or password.")
            self.password.delete(0, "end")


class CrudTab(ttk.Frame):
    """Reusable Add / Update / Delete / Search tab. Children only set the config."""

    record_cls = Record
    fields = []    
    headings = [] 
    list_sql = ""
    FORM_COLUMNS = 4 

    def __init__(self, parent, db):
        super().__init__(parent, padding=(16, 12))
        self.db = db
        self.selected_id = None
        self.vars, self.boxes = {}, {}

        form = ttk.LabelFrame(self, text="Details", padding=12, style="Card.TLabelframe")
        form.pack(fill="x")
        for i, (col, label, kind, extra) in enumerate(self.fields):
            r, c = divmod(i, self.FORM_COLUMNS)
            ttk.Label(form, text=label, style="Card.TLabel").grid(
                row=r * 2, column=c, sticky="w", padx=6, pady=(4, 0))
            var = tk.StringVar()
            self.vars[col] = var
            if kind == "text":
                box = ttk.Entry(form, textvariable=var, width=22)
            else:
                box = ttk.Combobox(form, textvariable=var, state="readonly", width=24,
                                   values=extra if kind == "combo" else [])
            box.grid(row=r * 2 + 1, column=c, padx=6, pady=(0, 4), sticky="w")
            self.boxes[col] = box

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=12)
        for text, style, cmd in [("Add", "Accent.TButton", self.add),
                                 ("Update", "Soft.TButton", self.update),
                                 ("Delete", "Danger.TButton", self.delete),
                                 ("Clear", "TButton", self.clear)]:
            ttk.Button(bar, text=text, style=style, command=cmd).pack(side="left", padx=(0, 6))
        self.extra_buttons(bar)
        self.search = tk.StringVar()
        self.search.trace_add("write", lambda *a: self.refresh_table())
        ttk.Entry(bar, textvariable=self.search, width=22).pack(side="right")
        ttk.Label(bar, text="Search").pack(side="right", padx=(0, 8))

        self.count = ttk.Label(self, text="", style="Muted.TLabel")
        self.count.pack(side="bottom", anchor="w", pady=(6, 0))
        names = [h for h, _ in self.headings]
        self.table = build_table(self, names)
        for title, width in self.headings:
            self.table.heading(title, text=title)
            self.table.column(title, width=width)
        self.table.bind("<<TreeviewSelect>>", self.on_select)
        self.clear()
        self.reload()

    def extra_buttons(self, bar):  # children can add their own buttons
        pass

    # --- data helpers ---
    def fk_choices(self, kind, sql):
        choices = [f"{r[0]} - {r[1]}" for r in self.db.query(sql)]
        return ["0 - None"] + choices if kind == "fk_opt" else choices

    def reload(self):
        """Called when the tab is shown, so dropdowns include newly added data."""
        for col, _, kind, extra in self.fields:
            if kind in ("fk", "fk_opt"):
                self.boxes[col]["values"] = self.fk_choices(kind, extra)
        self.refresh_table()

    def refresh_table(self):
        q = self.search.get().lower()
        rows = [row for row in self.db.query(self.list_sql)
                if q in " ".join(str(v) for v in row).lower()]
        fill_table(self.table, rows)
        self.count.config(text=f"{len(rows)} record{'s' if len(rows) != 1 else ''}")

    def clear(self):
        self.selected_id = None
        for col, _, kind, extra in self.fields:
            if col == "date":
                self.vars[col].set(date.today().isoformat())
            elif kind == "combo":
                self.vars[col].set(extra[0])
            elif kind == "fk_opt":
                self.vars[col].set("0 - None")
            else:
                self.vars[col].set("")

    def on_select(self, _event):
        sel = self.table.selection()
        if not sel:
            return
        self.selected_id = self.table.item(sel[0])["values"][0]
        cols = ", ".join(c for c, *_ in self.fields)
        row = self.db.query(
            f"SELECT {cols} FROM {self.record_cls.table} WHERE id=?", (self.selected_id,))[0]
        for (col, _, kind, extra), value in zip(self.fields, row):
            if kind in ("fk", "fk_opt"):
                value = value or 0
                match = [c for c in self.fk_choices(kind, extra) if c.startswith(f"{value} - ")]
                value = match[0] if match else ""
            self.vars[col].set(value)

    def collect(self):
        data = {}
        for col, _, kind, _ in self.fields:
            value = self.vars[col].get()
            data[col] = value.split(" - ")[0] if kind in ("fk", "fk_opt") else value
        return self.record_cls(self.selected_id, **data)

    # --- CRUD actions ---
    def _run(self, action):
        try:
            action()
            self.reload()
            self.clear()
        except ValueError as e:
            messagebox.showwarning("Invalid input", str(e))
        except sqlite3.IntegrityError:
            messagebox.showerror("Not allowed",
                                 "Duplicate entry, or this record is still used by another record.")
        except sqlite3.Error as e:
            messagebox.showerror("Database error", str(e))

    def need_selection(self, action_name):
        if self.selected_id is None:
            messagebox.showinfo(action_name, "Select a row from the table first.")
            return False
        return True

    def add(self):
        self._run(lambda: self.db.insert(self.collect()))

    def update(self):
        if self.need_selection("Update"):
            self._run(lambda: self.db.update(self.collect()))

    def delete(self):
        if self.need_selection("Delete") and messagebox.askyesno("Confirm", "Delete this record?"):
            self._run(lambda: self.db.delete(self.record_cls.table, self.selected_id))


class CustomersTab(CrudTab):
    record_cls = Customer
    fields = [("name", "Full name", "text", None), ("phone", "Phone", "text", None)]
    headings = [("ID", 50), ("Name", 300), ("Phone", 150)]
    list_sql = "SELECT id, name, phone FROM customers ORDER BY id"


class VehiclesTab(CrudTab):
    record_cls = Vehicle
    fields = [("customer_id", "Owner", "fk", "SELECT id, name FROM customers"),
              ("plate", "Plate no.", "text", None),
              ("model", "Make / Model", "text", None),
              ("year", "Year", "text", None)]
    headings = [("ID", 50), ("Owner", 200), ("Plate", 120), ("Model", 200), ("Year", 80)]
    list_sql = """SELECT v.id, c.name, v.plate, v.model, v.year
                  FROM vehicles v JOIN customers c ON c.id = v.customer_id ORDER BY v.id"""


class ServicesTab(CrudTab):
    record_cls = ServiceOrder
    fields = [("vehicle_id", "Vehicle", "fk",
               "SELECT v.id, v.plate || ' (' || c.name || ')' FROM vehicles v "
               "JOIN customers c ON c.id = v.customer_id"),
              ("mechanic_id", "Assign mechanic", "fk_opt", "SELECT id, name FROM mechanics"),
              ("description", "Service / Problem", "text", None),
              ("cost", "Cost", "text", None),
              ("status", "Status", "combo", STATUSES),
              ("date", "Date", "text", None)]
    headings = [("ID", 40), ("Plate", 90), ("Owner", 130), ("Mechanic", 120),
                ("Service", 200), ("Cost", 80), ("Status", 100), ("Date", 100)]
    list_sql = f"""SELECT s.id, v.plate, c.name, COALESCE(m.name, '-'), s.description,
                          s.cost, s.status, s.date {SERVICE_JOIN} ORDER BY s.id DESC"""


class PartsTab(CrudTab):
    record_cls = Part
    fields = [("name", "Part name", "text", None), ("price", "Price", "text", None),
              ("stock", "Stock qty", "text", None)]
    headings = [("ID", 50), ("Part", 280), ("Price", 100), ("Stock", 100)]
    list_sql = "SELECT id, name, price, stock FROM parts ORDER BY id"

    def extra_buttons(self, bar):
        ttk.Button(bar, text="Update Stock", style="Soft.TButton",
                   command=self.update_stock).pack(side="left", padx=(0, 6))

    def update_stock(self):
        """Changes only the stock quantity of the selected part."""
        if not self.need_selection("Update Stock"):
            return
        try:
            qty = int(self.vars["stock"].get())
            if qty < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid input", "Stock must be a whole number, 0 or more.")
            return
        self.db.execute("UPDATE parts SET stock=? WHERE id=?", (qty, self.selected_id))
        self.reload()
        self.clear()


class MechanicsTab(CrudTab):
    record_cls = Mechanic
    fields = [("name", "Full name", "text", None), ("phone", "Phone", "text", None),
              ("specialty", "Specialty", "text", None)]
    headings = [("ID", 50), ("Name", 220), ("Phone", 130), ("Specialty", 180), ("Jobs assigned", 110)]
    list_sql = """SELECT m.id, m.name, m.phone, m.specialty, COUNT(s.id)
                  FROM mechanics m LEFT JOIN services s ON s.mechanic_id = m.id
                  GROUP BY m.id ORDER BY m.id"""


class PaymentsTab(CrudTab):
    record_cls = Payment
    fields = [("service_id", "Service", "fk",
               "SELECT s.id, v.plate || ': ' || s.description FROM services s "
               "JOIN vehicles v ON v.id = s.vehicle_id"),
              ("amount", "Amount", "text", None),
              ("method", "Method", "combo", PAY_METHODS),
              ("date", "Date", "text", None)]
    headings = [("ID", 50), ("Customer", 170), ("Plate", 100), ("Service", 190),
                ("Amount", 90), ("Method", 80), ("Date", 90)]
    list_sql = """SELECT p.id, c.name, v.plate, s.description, p.amount, p.method, p.date
                  FROM payments p JOIN services s ON s.id = p.service_id
                  JOIN vehicles v ON v.id = s.vehicle_id
                  JOIN customers c ON c.id = v.customer_id ORDER BY p.id DESC"""

    def extra_buttons(self, bar):
        ttk.Button(bar, text="Generate Receipt", style="Soft.TButton",
                   command=self.receipt).pack(side="left", padx=(0, 6))

    def receipt(self):
        if not self.need_selection("Receipt"):
            return
        pid, pdate, customer, plate, model, service, amount, method = self.db.query(
            """SELECT p.id, p.date, c.name, v.plate, v.model, s.description, p.amount, p.method
               FROM payments p JOIN services s ON s.id = p.service_id
               JOIN vehicles v ON v.id = s.vehicle_id
               JOIN customers c ON c.id = v.customer_id WHERE p.id=?""",
            (self.selected_id,))[0]
        text = (f"{'IVSMS OFFICIAL RECEIPT':^40}\n{'=' * 40}\n"
                f"Receipt No : {pid:05d}\nDate       : {pdate}\n"
                f"Customer   : {customer}\nVehicle    : {plate} ({model})\n"
                f"Service    : {service}\nPaid via   : {method}\n{'-' * 40}\n"
                f"TOTAL PAID : PHP {amount:,.2f}\n{'=' * 40}\n{'Thank you!':^40}\n")
        win = tk.Toplevel(self)
        win.title(f"Receipt #{pid:05d}")
        win.configure(bg=BG)
        win.resizable(False, False)
        box = tk.Text(win, width=42, height=14, font=("Courier", 10), bg="#FFFDF7",
                      fg=INK, relief="flat", padx=14, pady=12,
                      highlightthickness=1, highlightbackground=BORDER)
        box.insert("1.0", text)
        box.config(state="disabled")
        box.pack(padx=16, pady=16)

        def save():
            path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Text file", "*.txt")])
            if path:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(text)

        ttk.Button(win, text="Save / Print as TXT", style="Accent.TButton",
                   command=save).pack(pady=(0, 16))


class HistoryTab(ttk.Frame):
    """Service History: search by customer or vehicle, then export."""

    HEADERS = ["ID", "Date", "Customer", "Plate", "Model", "Service", "Mechanic", "Cost", "Status"]
    SQL = f"""SELECT s.id, s.date, c.name, v.plate, v.model, s.description,
                     COALESCE(m.name, '-'), s.cost, s.status
              {SERVICE_JOIN} ORDER BY s.date DESC, s.id DESC"""

    def __init__(self, parent, db):
        super().__init__(parent, padding=(16, 12))
        self.db = db
        self.shown = []
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 12))
        ttk.Label(bar, text="Search by customer or vehicle").pack(side="left")
        self.search = tk.StringVar()
        self.search.trace_add("write", lambda *a: self.reload())
        ttk.Entry(bar, textvariable=self.search, width=26).pack(side="left", padx=8)
        ttk.Button(bar, text="Export / Print Report", style="Accent.TButton",
                   command=lambda: export_csv(self.HEADERS, self.shown)).pack(side="right")
        self.table = build_table(self, self.HEADERS, height=16)
        for h in self.HEADERS:
            self.table.heading(h, text=h)
            self.table.column(h, width=40 if h == "ID" else 100)
        self.reload()

    def reload(self):
        q = self.search.get().lower()
        # customer, plate, model
        self.shown = [row for row in self.db.query(self.SQL)
                      if q in f"{row[2]} {row[3]} {row[4]}".lower()]
        fill_table(self.table, self.shown)


class ReportsTab(ttk.Frame):
    REPORTS = {
        "Customers": "SELECT id, name, phone FROM customers",
        "Vehicles": """SELECT v.id, c.name AS owner, v.plate, v.model, v.year
                       FROM vehicles v JOIN customers c ON c.id = v.customer_id""",
        "Services": f"""SELECT s.id, s.date, c.name AS customer, v.plate, s.description,
                               COALESCE(m.name, '-') AS mechanic, s.cost, s.status
                        {SERVICE_JOIN}""",
        "Parts": "SELECT id, name, price, stock FROM parts",
        "Mechanics": "SELECT id, name, phone, specialty FROM mechanics",
        "Payments": """SELECT p.id, p.date, c.name AS customer, v.plate, p.amount, p.method
                       FROM payments p JOIN services s ON s.id = p.service_id
                       JOIN vehicles v ON v.id = s.vehicle_id
                       JOIN customers c ON c.id = v.customer_id""",
    }

    def __init__(self, parent, db):
        super().__init__(parent, padding=(16, 12))
        self.db = db
        self.headers, self.rows = [], []
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 12))
        ttk.Label(bar, text="Report type").pack(side="left")
        self.choice = tk.StringVar(value="Services")
        ttk.Combobox(bar, textvariable=self.choice, values=list(self.REPORTS),
                     state="readonly", width=16).pack(side="left", padx=8)
        ttk.Button(bar, text="Generate Report", style="Accent.TButton",
                   command=self.generate).pack(side="left", padx=4)
        ttk.Button(bar, text="Export to CSV", style="Soft.TButton",
                   command=lambda: export_csv(self.headers, self.rows)).pack(side="left", padx=4)
        self.table = build_table(self, [], height=16)

    def reload(self):
        pass

    def generate(self):
        self.headers, self.rows = self.db.query_with_headers(self.REPORTS[self.choice.get()])
        self.table["columns"] = self.headers
        for h in self.headers:
            self.table.heading(h, text=h.title())
            self.table.column(h, width=110)
        fill_table(self.table, self.rows)


class DashboardTab(ttk.Frame):
    # (label, sql, accent colour)
    STATS = [
        ("Customers", "SELECT COUNT(*) FROM customers", INK),
        ("Vehicles", "SELECT COUNT(*) FROM vehicles", INK),
        ("Mechanics", "SELECT COUNT(*) FROM mechanics", INK),
        ("Open jobs", "SELECT COUNT(*) FROM services WHERE status != 'Completed'", "#1971C2"),
        ("Completed jobs", "SELECT COUNT(*) FROM services WHERE status = 'Completed'", "#2B8A3E"),
        (f"Low-stock parts (<= {LOW_STOCK})",
         f"SELECT COUNT(*) FROM parts WHERE stock <= {LOW_STOCK}", DANGER),
        ("Payments received", "SELECT COALESCE(SUM(amount), 0) FROM payments", ACCENT),
    ]
    RECENT_SQL = f"""SELECT s.date, v.plate, c.name, s.description, s.status
                     {SERVICE_JOIN} ORDER BY s.id DESC LIMIT 8"""

    def __init__(self, parent, db):
        super().__init__(parent, padding=(20, 16))
        self.db = db
        self.values = {}

        ttk.Label(self, text="Shop overview", style="Title.TLabel").pack(anchor="w")
        ttk.Label(self, text=date.today().strftime("%A, %B %d, %Y"),
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 14))

        grid = ttk.Frame(self)
        grid.pack(fill="x")
        for i in range(4):
            grid.columnconfigure(i, weight=1, uniform="card")
        for i, (label, _, color) in enumerate(self.STATS):
            card = tk.Frame(grid, bg=CARD, highlightthickness=1, highlightbackground=BORDER)
            card.grid(row=i // 4, column=i % 4, padx=6, pady=6, sticky="nsew")
            tk.Frame(card, bg=color, width=5).pack(side="left", fill="y")
            body = tk.Frame(card, bg=CARD)
            body.pack(side="left", fill="both", expand=True, padx=14, pady=12)
            self.values[label] = tk.Label(body, text="0", font=f(22, True), fg=color,
                                          bg=CARD, anchor="w")
            self.values[label].pack(fill="x")
            tk.Label(body, text=label, font=f(9), fg=MUTED, bg=CARD, anchor="w").pack(fill="x")

        ttk.Label(self, text="Latest services", font=f(12, True)).pack(anchor="w", pady=(18, 6))
        cols = ["Date", "Plate", "Customer", "Service", "Status"]
        self.recent = build_table(self, cols, height=8)
        for c, w in zip(cols, (100, 100, 180, 280, 110)):
            self.recent.heading(c, text=c)
            self.recent.column(c, width=w)
        self.reload()

    def reload(self):
        for label, sql, _ in self.STATS:
            value = self.db.query(sql)[0][0]
            if label == "Payments received":
                value = f"PHP {float(value):,.2f}"
            self.values[label].config(text=value)
        fill_table(self.recent, self.db.query(self.RECENT_SQL))


class MainWindow(BaseWindow):
    TABS = [("Dashboard", DashboardTab), ("Customers", CustomersTab),
            ("Vehicles", VehiclesTab), ("Service", ServicesTab),
            ("Parts", PartsTab), ("Mechanics", MechanicsTab),
            ("Payments", PaymentsTab), ("Service History", HistoryTab),
            ("Reports", ReportsTab)]

    def __init__(self, db):
        self.db = db
        super().__init__("Integrated Vehicle Service Management System (IVSMS)", 1100, 700)

    def build_ui(self):
        top = tk.Frame(self, bg=INK)
        top.pack(fill="x")
        tk.Frame(top, bg=ACCENT, height=4).pack(fill="x")
        row = tk.Frame(top, bg=INK)
        row.pack(fill="x", padx=16, pady=10)
        tk.Label(row, text="IVSMS", font=f(16, True), fg=ACCENT, bg=INK).pack(side="left")
        tk.Label(row, text="Vehicle Service Management", font=f(10), fg="#CBD2D9",
                 bg=INK).pack(side="left", padx=12)
        ttk.Button(row, text="Logout", style="Top.TButton", command=self.logout).pack(side="right")
        tk.Label(row, text="Signed in as admin", font=f(9), fg="#9AA5B1",
                 bg=INK).pack(side="right", padx=14)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        for title, tab_cls in self.TABS:
            self.notebook.add(tab_cls(self.notebook, self.db), text=title)
        self.notebook.bind("<<NotebookTabChanged>>",
                           lambda e: self.nametowidget(self.notebook.select()).reload())

    def logout(self):
        if messagebox.askyesno("Logout", "End session and log out?"):
            self.destroy()
            LoginWindow(self.db).mainloop()


if __name__ == "__main__":
    LoginWindow(Database()).mainloop()