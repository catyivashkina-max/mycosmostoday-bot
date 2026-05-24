import sqlite3


DB_NAME = "users.db"


def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            birth_date TEXT,
            birth_time TEXT,
            birth_city TEXT,
            astro_profile TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]

    if "astro_profile" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN astro_profile TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forecasts (
            telegram_id INTEGER,
            forecast_date TEXT,
            birth_date TEXT,
            birth_time TEXT,
            birth_city TEXT,
            forecast_text TEXT,
            PRIMARY KEY (
                telegram_id,
                forecast_date,
                birth_date,
                birth_time,
                birth_city
            )
        )
    """)

    conn.commit()
    conn.close()


def save_user(telegram_id: int, birth_date: str, birth_time: str, birth_city: str, astro_profile: str = None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (telegram_id, birth_date, birth_time, birth_city, astro_profile)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            birth_date = excluded.birth_date,
            birth_time = excluded.birth_time,
            birth_city = excluded.birth_city,
            astro_profile = excluded.astro_profile
    """, (telegram_id, birth_date, birth_time, birth_city, astro_profile))

    conn.commit()
    conn.close()


def get_user(telegram_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT birth_date, birth_time, birth_city, astro_profile
        FROM users
        WHERE telegram_id = ?
    """, (telegram_id,))

    user = cursor.fetchone()

    conn.close()
    return user

def save_forecast(
    telegram_id: int,
    forecast_date: str,
    birth_date: str,
    birth_time: str,
    birth_city: str,
    forecast_text: str
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO forecasts (
            telegram_id,
            forecast_date,
            birth_date,
            birth_time,
            birth_city,
            forecast_text
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(
            telegram_id,
            forecast_date,
            birth_date,
            birth_time,
            birth_city
        ) DO UPDATE SET
            forecast_text = excluded.forecast_text
    """, (
        telegram_id,
        forecast_date,
        birth_date,
        birth_time,
        birth_city,
        forecast_text
    ))

    conn.commit()
    conn.close()


def get_forecast(
    telegram_id: int,
    forecast_date: str,
    birth_date: str,
    birth_time: str,
    birth_city: str
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT forecast_text
        FROM forecasts
        WHERE telegram_id = ?
          AND forecast_date = ?
          AND birth_date = ?
          AND birth_time = ?
          AND birth_city = ?
    """, (
        telegram_id,
        forecast_date,
        birth_date,
        birth_time,
        birth_city
    ))

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return None

