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

    c.execute("""
        CREATE TABLE IF NOT EXISTS exercise_logs (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER NOT NULL,
            activity_name    TEXT    NOT NULL,
            duration_min     INTEGER NOT NULL,
            calories_burned  INTEGER NOT NULL DEFAULT 0,
            intensity        TEXT    NOT NULL DEFAULT 'Moderate',
            logged_at        TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            title       TEXT    NOT NULL,
            ingredients TEXT    NOT NULL DEFAULT '',
            instructions TEXT   NOT NULL DEFAULT '',
            calories    INTEGER NOT NULL DEFAULT 0,
            carbs       INTEGER NOT NULL DEFAULT 0,
            protein     INTEGER NOT NULL DEFAULT 0,
            fat         INTEGER NOT NULL DEFAULT 0,
            diet        TEXT    NOT NULL DEFAULT '',
            source_food TEXT    NOT NULL DEFAULT '',
            saved_at    TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS nutritional_fingerprints (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL UNIQUE,
            vector       TEXT    NOT NULL DEFAULT '[]',
            alpha        REAL    NOT NULL DEFAULT 0.15,
            last_updated TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS rl_transitions (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER NOT NULL,
            date             TEXT    NOT NULL DEFAULT (date('now')),
            old_goal         INTEGER NOT NULL,
            new_goal         INTEGER NOT NULL,
            action_kcal      INTEGER NOT NULL,
            reward           REAL    NOT NULL,
            adherence_ratio  REAL    NOT NULL,
            weight_delta     REAL    NOT NULL,
            log_consistency  REAL    NOT NULL,
            reason           TEXT    NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS meal_plans (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            title        TEXT    NOT NULL DEFAULT '',
            week_start   TEXT    NOT NULL,
            diet         TEXT    NOT NULL DEFAULT '',
            daily_goal   INTEGER NOT NULL DEFAULT 2000,
            plan_json    TEXT    NOT NULL DEFAULT '{}',
            grocery_json TEXT    NOT NULL DEFAULT '{}',
            created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS lstm_models (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL UNIQUE,
            weights_json TEXT    NOT NULL DEFAULT '{}',
            last_trained TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS micronutrient_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            food_log_id INTEGER,
            iron        REAL NOT NULL DEFAULT 0,
            calcium     REAL NOT NULL DEFAULT 0,
            vitamin_c   REAL NOT NULL DEFAULT 0,
            vitamin_d   REAL NOT NULL DEFAULT 0,
            fiber       REAL NOT NULL DEFAULT 0,
            sodium      REAL NOT NULL DEFAULT 0,
            sugar       REAL NOT NULL DEFAULT 0,
            logged_at   TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (food_log_id) REFERENCES food_logs(id)
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


# ─── EXERCISE LOGS ─────────────────────────────────────

def add_exercise_log(user_id: int, activity_name: str, duration_min: int,
                     calories_burned: int = 0, intensity: str = "Moderate"):
    conn = get_connection()
    conn.execute(
        """INSERT INTO exercise_logs
           (user_id, activity_name, duration_min, calories_burned, intensity)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, activity_name, duration_min, calories_burned, intensity),
    )
    conn.commit()
    conn.close()


def get_exercise_logs_range(user_id: int, days: int = 30) -> list[dict]:
    """Return exercise log rows for the past N days."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM exercise_logs
           WHERE user_id = ?
             AND logged_at >= date('now', ?)
           ORDER BY logged_at""",
        (user_id, f"-{days} days"),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_daily_exercise_summary(user_id: int, days: int = 14) -> list[dict]:
    """Return per-day exercise totals for the last N days."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT date(logged_at) AS day,
                  COUNT(*) AS sessions,
                  COALESCE(SUM(duration_min), 0) AS total_minutes,
                  COALESCE(SUM(calories_burned), 0) AS total_burned
           FROM exercise_logs
           WHERE user_id = ?
             AND logged_at >= date('now', ?)
           GROUP BY day
           ORDER BY day""",
        (user_id, f"-{days} days"),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


# ─── EXTENDED QUERY HELPERS ────────────────────────────

def get_food_logs_by_date(user_id: int, date_str: str) -> list[dict]:
    """Return food logs for a specific date (YYYY-MM-DD)."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM food_logs
           WHERE user_id = ? AND date(logged_at) = ?
           ORDER BY logged_at""",
        (user_id, date_str),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def delete_food_log(log_id: int, user_id: int):
    """Delete a single food log entry (user_id prevents cross-user deletion)."""
    conn = get_connection()
    conn.execute(
        "DELETE FROM food_logs WHERE id = ? AND user_id = ?",
        (log_id, user_id),
    )
    conn.commit()
    conn.close()


def get_daily_calorie_summary(user_id: int, days: int = 14) -> list[dict]:
    """Return per-day calorie totals for the last N days."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT date(logged_at) AS day, SUM(calories) AS total_cals,
                  SUM(carbs) AS total_carbs, SUM(protein) AS total_protein,
                  SUM(fat) AS total_fat
           FROM food_logs
           WHERE user_id = ?
             AND logged_at >= date('now', ?)
           GROUP BY day
           ORDER BY day""",
        (user_id, f"-{days} days"),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_hydration_by_date(user_id: int, date_str: str) -> int:
    """Return total ml consumed on a specific date."""
    conn = get_connection()
    row = conn.execute(
        """SELECT COALESCE(SUM(amount_ml), 0) AS total
           FROM hydration_logs
           WHERE user_id = ? AND date(logged_at) = ?""",
        (user_id, date_str),
    ).fetchone()
    total = row["total"]
    conn.close()
    return total


def get_daily_hydration_summary(user_id: int, days: int = 14) -> list[dict]:
    """Return per-day hydration totals for the last N days."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT date(logged_at) AS day, SUM(amount_ml) AS total_ml
           FROM hydration_logs
           WHERE user_id = ?
             AND logged_at >= date('now', ?)
           GROUP BY day
           ORDER BY day""",
        (user_id, f"-{days} days"),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


# ─── ANALYTICS QUERIES ─────────────────────────────────

def get_meal_distribution(user_id: int, days: int = 30) -> list[dict]:
    """Return total calories and entry count grouped by meal category."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT meal,
                  COUNT(*)       AS entry_count,
                  SUM(calories)  AS total_cals
           FROM food_logs
           WHERE user_id = ?
             AND logged_at >= date('now', ?)
           GROUP BY meal
           ORDER BY total_cals DESC""",
        (user_id, f"-{days} days"),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_all_food_logs_range(user_id: int, days: int = 30) -> list[dict]:
    """Return every food log row for the past N days."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM food_logs
           WHERE user_id = ?
             AND logged_at >= date('now', ?)
           ORDER BY logged_at""",
        (user_id, f"-{days} days"),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_streak_and_totals(user_id: int) -> dict:
    """Return lifetime stats: total logs, total calories, active days, streak."""
    conn = get_connection()

    totals = conn.execute(
        """SELECT COUNT(*) AS total_entries,
                  COALESCE(SUM(calories), 0) AS total_cals
           FROM food_logs WHERE user_id = ?""",
        (user_id,),
    ).fetchone()

    # Days with at least one log
    days_rows = conn.execute(
        """SELECT DISTINCT date(logged_at) AS day
           FROM food_logs WHERE user_id = ?
           ORDER BY day DESC""",
        (user_id,),
    ).fetchall()
    conn.close()

    active_days = len(days_rows)
    streak = 0
    if days_rows:
        today = datetime.date.today()
        for i, row in enumerate(days_rows):
            expected = (today - datetime.timedelta(days=i)).isoformat()
            if row["day"] == expected:
                streak += 1
            else:
                break

    return {
        "total_entries": totals["total_entries"],
        "total_cals":    totals["total_cals"],
        "active_days":   active_days,
        "streak":        streak,
    }


# ─── RECIPES ───────────────────────────────────────────

def save_recipe(user_id: int, title: str, ingredients: str,
                instructions: str, calories: int, carbs: int,
                protein: int, fat: int, diet: str, source_food: str):
    conn = get_connection()
    conn.execute(
        """INSERT INTO recipes
           (user_id, title, ingredients, instructions, calories,
            carbs, protein, fat, diet, source_food)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, title, ingredients, instructions, calories,
         carbs, protein, fat, diet, source_food),
    )
    conn.commit()
    conn.close()


def get_saved_recipes(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM recipes WHERE user_id = ? ORDER BY saved_at DESC",
        (user_id,),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def delete_recipe(recipe_id: int, user_id: int):
    conn = get_connection()
    conn.execute(
        "DELETE FROM recipes WHERE id = ? AND user_id = ?",
        (recipe_id, user_id),
    )
    conn.commit()
    conn.close()


# ─── NUTRITIONAL FINGERPRINTS ──────────────────────────

def get_fingerprint(user_id: int) -> list[float]:
    """Return the stored 10-dimensional fingerprint vector, or ten zeros."""
    import json
    conn = get_connection()
    row = conn.execute(
        "SELECT vector FROM nutritional_fingerprints WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    if row and row["vector"]:
        try:
            vec = json.loads(row["vector"])
            if isinstance(vec, list) and len(vec) == 10:
                return [float(v) for v in vec]
        except (json.JSONDecodeError, ValueError):
            pass
    return [0.0] * 10


def save_fingerprint(user_id: int, vector: list[float]):
    """Upsert the fingerprint vector for a user."""
    import json
    vec_json = json.dumps([round(v, 6) for v in vector])
    now = datetime.datetime.now().isoformat()
    conn = get_connection()
    conn.execute(
        """INSERT INTO nutritional_fingerprints (user_id, vector, last_updated)
           VALUES (?, ?, ?)
           ON CONFLICT(user_id) DO UPDATE
           SET vector = excluded.vector, last_updated = excluded.last_updated""",
        (user_id, vec_json, now),
    )
    conn.commit()
    conn.close()


def get_fingerprint_history(user_id: int, days: int = 14) -> list[dict]:
    """Per-day aggregated food log totals for the past N days."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT date(logged_at) AS day,
                  COALESCE(SUM(calories), 0) AS total_cals,
                  COALESCE(SUM(protein), 0)  AS total_protein,
                  COALESCE(SUM(carbs), 0)    AS total_carbs,
                  COALESCE(SUM(fat), 0)      AS total_fat,
                  COUNT(*)                   AS meals_logged
           FROM food_logs
           WHERE user_id = ?
             AND logged_at >= date('now', ?)
           GROUP BY day
           ORDER BY day""",
        (user_id, f"-{days} days"),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


# ─── RL TRANSITIONS ────────────────────────────────────

def log_rl_transition(user_id: int, old_goal: int, new_goal: int,
                      action_kcal: int, reward: float, adherence_ratio: float,
                      weight_delta: float, log_consistency: float, reason: str):
    """Insert one row into rl_transitions."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO rl_transitions
           (user_id, old_goal, new_goal, action_kcal, reward,
            adherence_ratio, weight_delta, log_consistency, reason)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, old_goal, new_goal, action_kcal, reward,
         adherence_ratio, weight_delta, log_consistency, reason),
    )
    conn.commit()
    conn.close()


def get_rl_history(user_id: int, days: int = 30) -> list[dict]:
    """Return rl_transitions for the given user within the last N days."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM rl_transitions
           WHERE user_id = ? AND date >= date('now', ?)
           ORDER BY date DESC""",
        (user_id, f"-{days} days"),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_last_rl_update_days(user_id: int) -> int:
    """Return how many days since the last RL transition for this user."""
    conn = get_connection()
    row = conn.execute(
        "SELECT MAX(date) AS last_date FROM rl_transitions WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    if row and row["last_date"]:
        last = datetime.date.fromisoformat(row["last_date"])
        return (datetime.date.today() - last).days
    return 99


# ─── MEAL PLANS ────────────────────────────────────────

def save_meal_plan(user_id: int, title: str, week_start: str,
                   diet: str, daily_goal: int,
                   plan_json: str, grocery_json: str):
    conn = get_connection()
    conn.execute(
        """INSERT INTO meal_plans
           (user_id, title, week_start, diet, daily_goal, plan_json, grocery_json)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, title, week_start, diet, daily_goal, plan_json, grocery_json),
    )
    conn.commit()
    conn.close()


def get_meal_plans(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM meal_plans WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def delete_meal_plan(plan_id: int, user_id: int):
    conn = get_connection()
    conn.execute(
        "DELETE FROM meal_plans WHERE id = ? AND user_id = ?",
        (plan_id, user_id),
    )
    conn.commit()
    conn.close()


# ─── LSTM MODEL PERSISTENCE ───────────────────────────

def save_lstm_weights(user_id: int, weights_json: str):
    now = datetime.datetime.now().isoformat()
    conn = get_connection()
    conn.execute(
        """INSERT INTO lstm_models (user_id, weights_json, last_trained)
           VALUES (?, ?, ?)
           ON CONFLICT(user_id) DO UPDATE
           SET weights_json = excluded.weights_json,
               last_trained = excluded.last_trained""",
        (user_id, weights_json, now),
    )
    conn.commit()
    conn.close()


def get_lstm_weights(user_id: int) -> str | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT weights_json FROM lstm_models WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return row["weights_json"] if row else None


# ─── MICRONUTRIENT LOGS ───────────────────────────────

def add_micronutrient_log(user_id: int, food_log_id: int, iron: float,
                          calcium: float, vitamin_c: float, vitamin_d: float,
                          fiber: float, sodium: float, sugar: float):
    conn = get_connection()
    conn.execute(
        """INSERT INTO micronutrient_logs
           (user_id, food_log_id, iron, calcium, vitamin_c, vitamin_d, fiber, sodium, sugar)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, food_log_id, iron, calcium, vitamin_c, vitamin_d, fiber, sodium, sugar),
    )
    conn.commit()
    conn.close()


def get_micronutrient_summary(user_id: int, days: int = 7) -> list[dict]:
    """Return per-day micronutrient totals for the last N days."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT date(logged_at) AS day,
                  COALESCE(SUM(iron), 0) AS iron,
                  COALESCE(SUM(calcium), 0) AS calcium,
                  COALESCE(SUM(vitamin_c), 0) AS vitamin_c,
                  COALESCE(SUM(vitamin_d), 0) AS vitamin_d,
                  COALESCE(SUM(fiber), 0) AS fiber,
                  COALESCE(SUM(sodium), 0) AS sodium,
                  COALESCE(SUM(sugar), 0) AS sugar
           FROM micronutrient_logs
           WHERE user_id = ?
             AND logged_at >= date('now', ?)
           GROUP BY day
           ORDER BY day""",
        (user_id, f"-{days} days"),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_last_food_log_id(user_id: int) -> int | None:
    """Return the id of the most recently inserted food log for a user."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM food_logs WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    return row["id"] if row else None


# ─── EXERCISE LOGS (MET-BASED) ────────────────────────

def get_exercise_logs_today(user_id: int) -> list[dict]:
    today = datetime.date.today().isoformat()
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM exercise_logs
           WHERE user_id = ? AND date(logged_at) = ?
           ORDER BY logged_at""",
        (user_id, today),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_net_calories_today(user_id: int) -> dict:
    """Return food calories, exercise burn, and net for today."""
    today = datetime.date.today().isoformat()
    conn = get_connection()
    food_row = conn.execute(
        """SELECT COALESCE(SUM(calories), 0) AS food_cals
           FROM food_logs WHERE user_id = ? AND date(logged_at) = ?""",
        (user_id, today),
    ).fetchone()
    ex_row = conn.execute(
        """SELECT COALESCE(SUM(calories_burned), 0) AS burned
           FROM exercise_logs WHERE user_id = ? AND date(logged_at) = ?""",
        (user_id, today),
    ).fetchone()
    conn.close()
    food_cals = food_row["food_cals"]
    burned = ex_row["burned"]
    return {"food_cals": food_cals, "burned": burned, "net": food_cals - burned}


def get_daily_net_calories(user_id: int, days: int = 14) -> list[dict]:
    """Return per-day food cals, exercise burn, and net for the last N days."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT day,
                  COALESCE(fc.total_cals, 0) AS food_cals,
                  COALESCE(ec.total_burned, 0) AS burned
           FROM (
               SELECT DISTINCT date(logged_at) AS day
               FROM food_logs WHERE user_id = ? AND logged_at >= date('now', ?)
               UNION
               SELECT DISTINCT date(logged_at) AS day
               FROM exercise_logs WHERE user_id = ? AND logged_at >= date('now', ?)
           ) days
           LEFT JOIN (
               SELECT date(logged_at) AS d, SUM(calories) AS total_cals
               FROM food_logs WHERE user_id = ? GROUP BY d
           ) fc ON fc.d = days.day
           LEFT JOIN (
               SELECT date(logged_at) AS d, SUM(calories_burned) AS total_burned
               FROM exercise_logs WHERE user_id = ? GROUP BY d
           ) ec ON ec.d = days.day
           ORDER BY day""",
        (user_id, f"-{days} days", user_id, f"-{days} days", user_id, user_id),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


# ─── ACHIEVEMENTS / GAMIFICATION ──────────────────────

def get_achievement_stats(user_id: int) -> dict:
    """Gather various stats needed to compute achievements."""
    conn = get_connection()

    streak_data = get_streak_and_totals(user_id)

    # Hydration perfect days (>= 3000 ml)
    hydration_days = conn.execute(
        """SELECT COUNT(*) AS cnt FROM (
               SELECT date(logged_at) AS d, SUM(amount_ml) AS total
               FROM hydration_logs WHERE user_id = ?
               GROUP BY d HAVING total >= 3000
           )""",
        (user_id,),
    ).fetchone()["cnt"]

    # Exercise sessions total
    ex_total = conn.execute(
        "SELECT COUNT(*) AS cnt FROM exercise_logs WHERE user_id = ?",
        (user_id,),
    ).fetchone()["cnt"]

    # Exercise streak (consecutive days)
    ex_days = conn.execute(
        """SELECT DISTINCT date(logged_at) AS day
           FROM exercise_logs WHERE user_id = ?
           ORDER BY day DESC""",
        (user_id,),
    ).fetchall()
    ex_streak = 0
    if ex_days:
        today = datetime.date.today()
        for i, row in enumerate(ex_days):
            expected = (today - datetime.timedelta(days=i)).isoformat()
            if row["day"] == expected:
                ex_streak += 1
            else:
                break

    # Weight logs count
    weight_count = conn.execute(
        "SELECT COUNT(*) AS cnt FROM weight_logs WHERE user_id = ?",
        (user_id,),
    ).fetchone()["cnt"]

    # Days under calorie goal
    user = get_user_by_id(user_id) or {}
    goal = user.get("daily_goal", 2000)
    under_goal_days = conn.execute(
        """SELECT COUNT(*) AS cnt FROM (
               SELECT date(logged_at) AS d, SUM(calories) AS total
               FROM food_logs WHERE user_id = ?
               GROUP BY d HAVING total <= ? AND total > 0
           )""",
        (user_id, goal),
    ).fetchone()["cnt"]

    conn.close()

    return {
        "total_entries": streak_data["total_entries"],
        "total_cals": streak_data["total_cals"],
        "active_days": streak_data["active_days"],
        "streak": streak_data["streak"],
        "hydration_perfect_days": hydration_days,
        "exercise_sessions": ex_total,
        "exercise_streak": ex_streak,
        "weight_logs": weight_count,
        "under_goal_days": under_goal_days,
    }


# ─── DATA EXPORT HELPERS ─────────────────────────────

def get_all_food_logs(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM food_logs WHERE user_id = ? ORDER BY logged_at",
        (user_id,),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_all_exercise_logs(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM exercise_logs WHERE user_id = ? ORDER BY logged_at",
        (user_id,),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_all_hydration_logs(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM hydration_logs WHERE user_id = ? ORDER BY logged_at",
        (user_id,),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_all_weight_logs(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM weight_logs WHERE user_id = ? ORDER BY logged_at",
        (user_id,),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result


def get_all_micronutrient_logs(user_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM micronutrient_logs WHERE user_id = ? ORDER BY logged_at",
        (user_id,),
    ).fetchall()
    result = [dict(r) for r in rows]
    conn.close()
    return result
