import sqlite3
from datetime import datetime

import sqlite3
import os

DB_NAME = os.getenv("DB_NAME", "users.db")

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


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            action TEXT,
            created_at TEXT
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

async def daily_reminder():
    while True:
        now = datetime.now()

        if now.hour == 9 and now.minute == 0:
            users = get_all_users()

            for user in users:
                telegram_id = user[0]

                try:
                    await bot.send_message(
                        telegram_id,
                        "Доброе утро ✨\n\n"
                        "Твой персональный прогноз на сегодня уже ждёт тебя 🌙",
                        reply_markup=main_keyboard()
                    )
                except Exception as e:
                    print(f"Не удалось отправить напоминание {telegram_id}: {e}")

            await asyncio.sleep(60)

        await asyncio.sleep(30)

def save_event(telegram_id: int, action: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO analytics (
            telegram_id,
            action,
            created_at
        )
        VALUES (?, ?, ?)
    """, (
        telegram_id,
        action,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    def get_stats():
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) 
            FROM analytics 
            WHERE action = 'start'
        """)
        starts_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) 
            FROM analytics 
            WHERE action = 'forecast'
        """)
        forecasts_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) 
            FROM analytics 
            WHERE action = 'astro_profile'
        """)
        profiles_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT telegram_id)
            FROM analytics
            WHERE date(created_at) = date('now')
        """)
        active_today = cursor.fetchone()[0]

        conn.close()

        return {
            "users_count": users_count,
            "starts_count": starts_count,
            "forecasts_count": forecasts_count,
            "profiles_count": profiles_count,
            "active_today": active_today
        }