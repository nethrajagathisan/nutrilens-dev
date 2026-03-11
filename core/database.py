import sqlite3
import os
import datetime

import bcrypt

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "nutrilens.db")


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL DEFAULT '',
            password_hash TEXT    NOT NULL DEFAULT '',
            name          TEXT    NOT NULL DEFAULT '',
            age           INTEGER NOT NULL DEFAULT 25,
            gender        TEXT    NOT NULL DEFAULT 'Male',
            weight_kg     REAL    NOT NULL DEFAULT 70,
            height_cm     REAL    NOT NULL DEFAULT 175,
            activity      TEXT    NOT NULL DEFAULT 'Active',
            diet          TEXT    NOT NULL DEFAULT 'Balanced',
            bmi           REAL    NOT NULL DEFAULT 0,
            daily_goal    INTEGER NOT NULL DEFAULT 2000,
            created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)
    _run_migrations(conn)

    c.execute("""
        CREATE TABLE IF NOT EXISTS food_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            name        TEXT    NOT NULL,
            calories    INTEGER NOT NULL,
            carbs       INTEGER NOT NULL DEFAULT 0,
            protein     INTEGER NOT NULL DEFAULT 0,
            fat         INTEGER NOT NULL DEFAULT 0,
            meal        TEXT    NOT NULL DEFAULT 'Snack',
            logged_at   TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS hydration_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            amount_ml   INTEGER NOT NULL,
            logged_at   TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS weight_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            weight_kg   REAL    NOT NULL,
            logged_at   TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def _run_migrations(conn):
    """Safely add new columns to existing databases without breaking old data."""
    new_cols = [
        "ALTER TABLE users ADD COLUMN username      TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE users ADD COLUMN password_hash TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE users ADD COLUMN name          TEXT NOT NULL DEFAULT ''",
    ]
    for sql in new_cols:
        try:
            conn.execute(sql)
        except Exception:
            pass  # Column already exists
    # Unique index only for non-empty usernames (partial index)
    try:
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username "
            "ON users(username) WHERE username != ''"
        )
    except Exception:
        pass
    conn.commit()


# ─── AUTH ──────────────────────────────────────────────

def register_user(username: str, password: str) -> dict | None:
    """Register a new user. Returns user dict on success, None if username taken."""
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()
    if existing:
        conn.close()
        return None
    hashed = _hash_password(password)
    conn.execute(
        "INSERT INTO users (username, password_hash, name) VALUES (?, ?, ?)",
        (username, hashed, username),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    result = dict(row)
    conn.close()
    return result


def authenticate_user(username: str, password: str) -> dict | None:
    """Verify credentials. Returns user dict on success, None on failure."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    user = dict(row)
    if not user["password_hash"] or not _verify_password(password, user["password_hash"]):
        return None
    return user


def get_user_by_id(user_id: int) -> dict | None:
    """Return a user row by primary key."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ─── USER ──────────────────────────────────────────────

def get_or_create_user(name: str = "default") -> dict:
    """Return the user row as a dict; create one if it doesn't exist."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchone()
    if row is None:
        conn.execute("INSERT INTO users (name) VALUES (?)", (name,))
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchone()
    result = dict(row)
    conn.close()
    return result


def update_user(user_id: int, **kwargs):
    """Update arbitrary user columns. Only whitelisted columns accepted."""
    allowed = {"age", "gender", "weight_kg", "height_cm", "activity",
               "diet", "bmi", "daily_goal", "name"}
    cols = {k: v for k, v in kwargs.items() if k in allowed}
    if not cols:
        return
    set_clause = ", ".join(f"{k} = ?" for k in cols)
    values = list(cols.values()) + [user_id]
    conn = get_connection()
    conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


# ─── FOOD LOGS ─────────────────────────────────────────

def add_food_log(user_id: int, name: str, calories: int,
                 carbs: int, protein: int, fat: int, meal: str):
    conn = get_connection()
    conn.execute(
        """INSERT INTO food_logs
           (user_id, name, calories, carbs, protein, fat, meal)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, name, calories, carbs, protein, fat, meal),
    )
    conn.commit()
    conn.close()


def get_food_logs_today(user_id: int) -> list[dict]:
    today = datetime.date.today().isoformat()
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM food_logs
           WHERE user_id = ? AND date(logged_at) = ?
           ORDER BY logged_at""",
        (user_id, today),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def clear_food_logs_today(user_id: int):
    today = datetime.date.today().isoformat()
    conn = get_connection()
    conn.execute(
        "DELETE FROM food_logs WHERE user_id = ? AND date(logged_at) = ?",
        (user_id, today),
    )
    conn.commit()
    conn.close()


# ─── HYDRATION LOGS ────────────────────────────────────

def add_hydration(user_id: int, amount_ml: int):
    conn = get_connection()
    conn.execute(
        "INSERT INTO hydration_logs (user_id, amount_ml) VALUES (?, ?)",
        (user_id, amount_ml),
    )
    conn.commit()
    conn.close()


def get_hydration_today(user_id: int) -> int:
    today = datetime.date.today().isoformat()
    conn = get_connection()
    row = conn.execute(
        """SELECT COALESCE(SUM(amount_ml), 0) AS total
           FROM hydration_logs
           WHERE user_id = ? AND date(logged_at) = ?""",
        (user_id, today),
    ).fetchone()
    total = row["total"]
    conn.close()
    return total


# ─── WEIGHT LOGS ───────────────────────────────────────

def add_weight_log(user_id: int, weight_kg: float):
    conn = get_connection()
    conn.execute(
        "INSERT INTO weight_logs (user_id, weight_kg) VALUES (?, ?)",
        (user_id, weight_kg),
    )
    conn.commit()
    conn.close()


def get_weight_history(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM weight_logs WHERE user_id = ? ORDER BY logged_at",
        (user_id,),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result
