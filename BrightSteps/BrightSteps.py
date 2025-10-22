"""
BrightSteps — Kindness & Habit Tracker with Login/SignUp (single-file)
Save as brightsteps.py and run: python brightsteps.py
Requires: matplotlib (pip install matplotlib)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import hashlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import Counter
import os

DB_PATH = "brightsteps.db"


# ---------------- Utility: simple password hashing ----------------
def hash_password(username: str, password: str) -> str:
    """Return a SHA-256 hash of username+password (simple salting by username)."""
    s = (username + password).encode("utf-8")
    return hashlib.sha256(s).hexdigest()


# ---------------- Database Initialization ----------------
def init_db():
    """Create required tables. If kindness_acts exists but lacks 'username', add the column."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Users table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # kindness_acts table with username field
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS kindness_acts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            description TEXT,
            date TEXT
        )
        """
    )

    # If 'username' column missing in older schema, add it.
    cur.execute("PRAGMA table_info(kindness_acts)")
    cols = [r[1] for r in cur.fetchall()]  # r[1] is column name
    if "username" not in cols:
        try:
            cur.execute("ALTER TABLE kindness_acts ADD COLUMN username TEXT")
        except sqlite3.OperationalError:
            # SQLite older versions may behave differently; ignore if fails
            pass

    conn.commit()
    conn.close()


# ---------------- Application (Frames + Navigation + Auth) ----------------
class BrightStepsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BrightSteps ☀️ — Kindness & Habit Tracker")
        # Mobile-ish tall window; adjust as you like
        self.geometry("420x700")
        self.configure(bg="#FFFBEA")
        self.resizable(False, False)

        init_db()
        self.current_user = None  # will store username after login
        self.active_frame = None

        # Start at Login screen
        self.show_frame(LoginScreen)

    def show_frame(self, frame_class, **kwargs):
        """Replace active frame with a new one (frame_class must accept parent and app)."""
        if self.active_frame:
            self.active_frame.destroy()
        self.active_frame = frame_class(self, self, **kwargs)
        self.active_frame.pack(fill="both", expand=True)

    def login_user(self, username: str):
        """Set the current user and open the main dashboard."""
        self.current_user = username
        self.show_frame(MainApp)


# ---------------- Login & Signup Screens ----------------
class LoginScreen(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg="#FFFBEA")
        self.app = app
        self.build_ui()

    def build_ui(self):
        padx = 30
        tk.Label(self, text="BrightSteps", font=("Nunito", 28, "bold"), bg="#FFFBEA", fg="#2B2B2B").pack(pady=(40, 5))
        tk.Label(self, text="Grow goodness, one step at a time", font=("Segoe UI", 10), bg="#FFFBEA").pack(pady=(0, 20))

        card = tk.Frame(self, bg="#FFF3C4", padx=20, pady=18, highlightbackground="#FFD56F", highlightthickness=1)
        card.pack(padx=padx, pady=10, fill="x")

        tk.Label(card, text="Login", bg="#FFF3C4", font=("Segoe UI", 14, "bold")).pack(anchor="w")

        tk.Label(card, text="Username", bg="#FFF3C4").pack(anchor="w", pady=(8, 2))
        self.username_var = tk.StringVar()
        tk.Entry(card, textvariable=self.username_var, font=("Segoe UI", 11)).pack(fill="x")

        tk.Label(card, text="Password", bg="#FFF3C4").pack(anchor="w", pady=(8, 2))
        self.password_var = tk.StringVar()
        tk.Entry(card, textvariable=self.password_var, font=("Segoe UI", 11), show="*").pack(fill="x")

        tk.Button(card, text="Login", bg="#F4A261", fg="white", font=("Segoe UI", 11, "bold"),
                  command=self.handle_login).pack(pady=12, fill="x")

        # Sign up prompt
        foot = tk.Frame(self, bg="#FFFBEA")
        foot.pack(pady=10)
        tk.Label(foot, text="New here?", bg="#FFFBEA").pack(side="left")
        tk.Button(foot, text="Create an account", bg="#FFFBEA", bd=0, fg="#F4A261",
                  command=lambda: self.app.show_frame(SignupScreen)).pack(side="left")

    def handle_login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        if not username or not password:
            messagebox.showwarning("Missing fields", "Please enter username and password.")
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()
        if not row:
            messagebox.showerror("Login failed", "No such user. Please sign up.")
            return

        stored_hash = row[0]
        if stored_hash == hash_password(username, password):
            messagebox.showinfo("Welcome", f"Welcome back, {username}!")
            self.app.login_user(username)
        else:
            messagebox.showerror("Login failed", "Incorrect password.")


class SignupScreen(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg="#FFFBEA")
        self.app = app
        self.build_ui()

    def build_ui(self):
        padx = 30
        tk.Label(self, text="Create account", font=("Nunito", 22, "bold"), bg="#FFFBEA", fg="#2B2B2B").pack(pady=(30, 8))
        tk.Label(self, text="Join BrightSteps and start your streak!", font=("Segoe UI", 10), bg="#FFFBEA").pack(pady=(0, 20))

        card = tk.Frame(self, bg="#FFF3C4", padx=20, pady=18, highlightbackground="#FFD56F", highlightthickness=1)
        card.pack(padx=padx, pady=10, fill="x")

        tk.Label(card, text="Username", bg="#FFF3C4").pack(anchor="w", pady=(0, 2))
        self.username_var = tk.StringVar()
        tk.Entry(card, textvariable=self.username_var, font=("Segoe UI", 11)).pack(fill="x")

        tk.Label(card, text="Password", bg="#FFF3C4").pack(anchor="w", pady=(8, 2))
        self.password_var = tk.StringVar()
        tk.Entry(card, textvariable=self.password_var, font=("Segoe UI", 11), show="*").pack(fill="x")

        tk.Label(card, text="Confirm Password", bg="#FFF3C4").pack(anchor="w", pady=(8, 2))
        self.confirm_var = tk.StringVar()
        tk.Entry(card, textvariable=self.confirm_var, font=("Segoe UI", 11), show="*").pack(fill="x")

        tk.Button(card, text="Create Account", bg="#F4A261", fg="white", font=("Segoe UI", 11, "bold"),
                  command=self.handle_signup).pack(pady=12, fill="x")

        tk.Button(self, text="Back to Login", bg="#FFFBEA", bd=0, fg="#F4A261", command=lambda: self.app.show_frame(LoginScreen)).pack(pady=6)

    def handle_signup(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        confirm = self.confirm_var.get().strip()

        if not username or not password or not confirm:
            messagebox.showwarning("Missing fields", "Please fill all fields.")
            return
        if password != confirm:
            messagebox.showerror("Mismatch", "Passwords do not match.")
            return

        pass_hash = hash_password(username, password)
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                        (username, pass_hash, created_at))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            messagebox.showerror("Signup failed", "Username already exists. Try another.")
            return

        messagebox.showinfo("Account created", "Your account was created successfully — welcome!")
        self.app.login_user(username)


# ---------------- Main App Container (Post-login) ----------------
class MainApp(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg="#FFFBEA")
        self.app = app
        self.username = app.current_user
        self.active_inner = None

        # Top bar with small logout button and greeting
        top = tk.Frame(self, bg="#FFFBEA")
        top.pack(fill="x", pady=(12, 4), padx=12)
        tk.Label(top, text=f"Hi {self.username} 💛", font=("Segoe UI", 16, "bold"), bg="#FFFBEA").pack(side="left")
        tk.Button(top, text="Logout", bg="#FFFBEA", bd=0, fg="#F4A261", command=self.logout).pack(side="right")

        # Container where Home/Overview/Progress will appear
        self.container = tk.Frame(self, bg="#FFFBEA")
        self.container.pack(fill="both", expand=True, padx=6, pady=(4, 60))

        # Bottom navbar
        navbar = tk.Frame(self, bg="#FFE8A3", height=60)
        navbar.pack(side="bottom", fill="x")

        buttons = [
            ("🏠", "Home", HomeScreen),
            ("🌟", "Overview", OverviewScreen),
            ("📈", "Progress", ProgressScreen)
        ]

        for icon, text, screen in buttons:
            btn = tk.Button(navbar, text=f"{icon}\n{text}", font=("Segoe UI", 10, "bold"),
                            bg="#FFE8A3", fg="#2B2B2B", bd=0,
                            activebackground="#FFCC70",
                            command=lambda s=screen: self.show_inner(s))
            btn.pack(side="left", expand=True, fill="both")

        # default inner screen
        self.show_inner(HomeScreen)

    def show_inner(self, frame_class):
        if self.active_inner:
            self.active_inner.destroy()
        # pass username to inner frames so they filter data
        self.active_inner = frame_class(self.container, self.app, username=self.username)
        self.active_inner.pack(fill="both", expand=True, pady=(0, 0))

    def logout(self):
        confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if confirm:
            self.app.current_user = None
            self.app.show_frame(LoginScreen)


# ---------------- Home / Overview / Progress Screens (updated to use username) ----------------
class HomeScreen(tk.Frame):
    def __init__(self, parent, app, username=None, **kwargs):
        super().__init__(parent, bg="#FFFBEA")
        self.app = app
        self.username = username
        self.build_ui()

    def build_ui(self):
        greeting = tk.Label(self, text=f"Welcome, {self.username} 💛", font=("Segoe UI", 16, "bold"), bg="#FFFBEA", fg="#2B2B2B")
        greeting.pack(pady=(6, 6))

        banner = tk.Label(
            self,
            text="Make a 30-day Kindness Streak!",
            bg="#FFB703", fg="white",
            font=("Segoe UI", 12, "bold"),
            padx=20, pady=10
        )
        banner.pack(pady=(0, 12), padx=16, fill="x")

        # Entry card
        card = tk.Frame(self, bg="#FFF3C4", bd=0, highlightbackground="#FFD56F", highlightthickness=1, padx=10, pady=10)
        card.pack(padx=16, pady=8, fill="x")

        tk.Label(card, text="🌼 Today’s Kind Act", bg="#FFF3C4", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.desc_entry = tk.Entry(card, font=("Segoe UI", 11))
        self.desc_entry.pack(fill="x", pady=8)

        tk.Button(
            card, text="➕ Add Kindness", bg="#F4A261", fg="white",
            font=("Segoe UI", 10, "bold"), command=self.add_kindness
        ).pack(pady=3)

        # Table of user's acts
        self.tree = ttk.Treeview(self, columns=("Description", "Date"), show="headings", height=9)
        self.tree.heading("Description", text="Description")
        self.tree.heading("Date", text="Date")
        self.tree.column("Description", width=260)
        self.tree.column("Date", width=100)
        self.tree.pack(padx=12, pady=12, fill="both", expand=True)

        self.load_entries()

    def add_kindness(self):
        desc = self.desc_entry.get().strip()
        if not desc:
            messagebox.showwarning("Input Error", "Please enter a kindness act description.")
            return
        date = datetime.now().strftime("%Y-%m-%d")
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO kindness_acts (username, description, date) VALUES (?, ?, ?)", (self.username, desc, date))
        conn.commit()
        conn.close()
        self.desc_entry.delete(0, tk.END)
        self.load_entries()
        messagebox.showinfo("Added", "🌸 Kindness recorded successfully!")

    def load_entries(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT description, date FROM kindness_acts WHERE username = ? ORDER BY id DESC", (self.username,))
        for r in cur.fetchall():
            self.tree.insert("", "end", values=r)
        conn.close()


class OverviewScreen(tk.Frame):
    def __init__(self, parent, app, username=None, **kwargs):
        super().__init__(parent, bg="#FFFBEA")
        self.app = app
        self.username = username
        self.build_ui()

    def build_ui(self):
        tk.Label(self, text="🌟 Monthly Overview", font=("Segoe UI", 16, "bold"), bg="#FFFBEA", fg="#2B2B2B").pack(pady=10)

        stats_frame = tk.Frame(self, bg="#FFF3C4", padx=14, pady=12, highlightbackground="#FFD56F", highlightthickness=1)
        stats_frame.pack(padx=14, pady=6, fill="x")

        total_acts = self.get_total_acts()
        stars = total_acts * 5
        streak = self.calculate_streak()

        tk.Label(stats_frame, text=f"Total Acts: {total_acts}", font=("Segoe UI", 11, "bold"), bg="#FFF3C4").pack(anchor="w")
        tk.Label(stats_frame, text=f"Stars Earned: ⭐ {stars}", font=("Segoe UI", 11, "bold"), bg="#FFF3C4").pack(anchor="w")
        tk.Label(stats_frame, text=f"Current Streak: 🔥 {streak} days", font=("Segoe UI", 11, "bold"), bg="#FFF3C4").pack(anchor="w")

        tk.Label(self, text="🎯 Missions", bg="#FFFBEA", font=("Segoe UI", 13, "bold")).pack(pady=(8, 4))
        missions = [
            "Do 3 acts this week → ⭐ +10",
            "Help a stranger → ⭐ +15",
            "Plant a tree → ⭐ +20"
        ]
        for m in missions:
            tk.Label(self, text=f"• {m}", bg="#FFFBEA", font=("Segoe UI", 10)).pack(anchor="w", padx=28)

        # Chart area
        self.show_chart()

    def get_total_acts(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM kindness_acts WHERE username = ?", (self.username,))
        total = cur.fetchone()[0]
        conn.close()
        return total

    def calculate_streak(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT date FROM kindness_acts WHERE username = ? ORDER BY date DESC", (self.username,))
        dates = [r[0] for r in cur.fetchall()]
        conn.close()

        if not dates:
            return 0

        streak = 1
        prev_date = datetime.strptime(dates[0], "%Y-%m-%d")
        for d in dates[1:]:
            current = datetime.strptime(d, "%Y-%m-%d")
            if (prev_date - current).days == 1:
                streak += 1
                prev_date = current
            else:
                break
        return streak

    def show_chart(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT date FROM kindness_acts WHERE username = ?", (self.username,))
        data = [r[0] for r in cur.fetchall()]
        conn.close()

        if not data:
            tk.Label(self, text="No data yet — add some acts to see trends!", bg="#FFFBEA").pack(pady=10)
            return

        counts = Counter(data)
        dates = sorted(counts.keys())
        values = [counts[d] for d in dates]

        fig, ax = plt.subplots(figsize=(3.6, 2.4), dpi=100)
        ax.plot(dates, values, marker='o')
        ax.set_title("Acts per Day", fontsize=10)
        ax.set_xlabel("Date")
        ax.set_ylabel("Acts")
        ax.grid(True, linestyle='--', alpha=0.4)
        fig.tight_layout()

        chart = FigureCanvasTkAgg(fig, self)
        chart.get_tk_widget().pack(pady=12)
        chart.draw()


class ProgressScreen(tk.Frame):
    def __init__(self, parent, app, username=None, **kwargs):
        super().__init__(parent, bg="#FFFBEA")
        self.app = app
        self.username = username
        self.build_ui()

    def build_ui(self):
        tk.Label(self, text="📈 Progress Dashboard", bg="#FFFBEA", font=("Segoe UI", 16, "bold")).pack(pady=18)
        tk.Label(self, text="Your kindness journey grows every day 🌱", bg="#FFFBEA", font=("Segoe UI", 11)).pack(pady=(0, 6))

        # Success rate - compute as ratio of days acted / total days tracked (simple metric)
        success_rate = self.calculate_success_rate()
        rate_frame = tk.Frame(self, bg="#FFF3C4", padx=18, pady=12, highlightbackground="#FFD56F", highlightthickness=1)
        rate_frame.pack(padx=22, pady=12)

        tk.Label(rate_frame, text=f"🌸 Success Rate: {success_rate}%", bg="#FFF3C4", font=("Segoe UI", 14, "bold")).pack()
        tk.Label(rate_frame, text=f"Shows % of days you logged at least one act", bg="#FFF3C4", font=("Segoe UI", 9)).pack()

        # Streaks
        best, current = self.best_and_current_streak()
        tk.Label(self, text=f"Best Streak: 🔥 {best} days", bg="#FFFBEA", font=("Segoe UI", 11)).pack(pady=(8, 2))
        tk.Label(self, text=f"Current Streak: 🔥 {current} days", bg="#FFFBEA", font=("Segoe UI", 11)).pack(pady=(0, 8))

    def calculate_success_rate(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT date FROM kindness_acts WHERE username = ?", (self.username,))
        days = [r[0] for r in cur.fetchall()]
        conn.close()
        if not days:
            return 0
        # Simple metric: days with acts / days since first act
        first = datetime.strptime(min(days), "%Y-%m-%d")
        days_since = (datetime.now() - first).days + 1
        rate = int(round(len(days) / days_since * 100))
        return rate

    def best_and_current_streak(self):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT date FROM kindness_acts WHERE username = ? ORDER BY date", (self.username,))
        dates = [r[0] for r in cur.fetchall()]
        conn.close()
        if not dates:
            return 0, 0

        # compute best streak
        best = 1
        current = 1
        prev = datetime.strptime(dates[0], "%Y-%m-%d")
        for d in dates[1:]:
            curd = datetime.strptime(d, "%Y-%m-%d")
            if (curd - prev).days == 1:
                current += 1
            else:
                best = max(best, current)
                current = 1
            prev = curd
        best = max(best, current)

        # compute current streak from latest day backwards
        dates_desc = sorted(dates, reverse=True)
        cur_streak = 1
        prev = datetime.strptime(dates_desc[0], "%Y-%m-%d")
        for d in dates_desc[1:]:
            curd = datetime.strptime(d, "%Y-%m-%d")
            if (prev - curd).days == 1:
                cur_streak += 1
                prev = curd
            else:
                break

        return best, cur_streak


# ---------------- Run the app ----------------
if __name__ == "__main__":
    # Ensure DB file exists next to script
    if not os.path.exists(DB_PATH):
        init_db()
    app = BrightStepsApp()
    app.mainloop()
