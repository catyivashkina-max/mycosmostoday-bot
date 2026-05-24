from openai import OpenAI
import os
from datetime import datetime


from dotenv import load_dotenv
from kerykeion import AstrologicalSubject
from geo import get_city_data

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SIGN_RU = {
    "Ari": "Овне", "Aries": "Овне",
    "Tau": "Тельце", "Taurus": "Тельце",
    "Gem": "Близнецах", "Gemini": "Близнецах",
    "Can": "Раке", "Cancer": "Раке",
    "Leo": "Льве",
    "Vir": "Деве", "Virgo": "Деве",
    "Lib": "Весах", "Libra": "Весах",
    "Sco": "Скорпионе", "Scorpio": "Скорпионе",
    "Sag": "Стрельце", "Sagittarius": "Стрельце",
    "Cap": "Козероге", "Capricorn": "Козероге",
    "Aqu": "Водолее", "Aquarius": "Водолее",
    "Pis": "Рыбах", "Pisces": "Рыбах",
}


def sign_ru(sign: str) -> str:
    return SIGN_RU.get(sign, sign)


def normalize_birth_time(birth_time: str):
    if birth_time.lower().strip() in ["не знаю", "не знаю.", "нет"]:
        return 12, 0, True

    hour, minute = birth_time.split(":")
    return int(hour), int(minute), False


def create_subject_from_birth(birth_date: str, birth_time: str, city: str):
    city_data = get_city_data(city)

    if not city_data:
        raise ValueError("city_not_found")

    day, month, year = birth_date.split(".")
    hour, minute, time_unknown = normalize_birth_time(birth_time)

    subject = AstrologicalSubject(
        name="User",
        year=int(year),
        month=int(month),
        day=int(day),
        hour=int(hour),
        minute=int(minute),
        city=city_data["name"],
        lat=city_data["lat"],
        lng=city_data["lng"],
        tz_str=city_data["timezone"]
    )

    return subject, city_data, time_unknown


def create_subject_for_today(city_data):
    now = datetime.utcnow()

    subject = AstrologicalSubject(
        name="Today",
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        minute=now.minute,
        city=city_data["name"],
        lat=city_data["lat"],
        lng=city_data["lng"],
        tz_str="UTC"
    )

    return subject, now


def get_house_cusps(natal_subject):
    return [
        (1, natal_subject.first_house.abs_pos),
        (2, natal_subject.second_house.abs_pos),
        (3, natal_subject.third_house.abs_pos),
        (4, natal_subject.fourth_house.abs_pos),
        (5, natal_subject.fifth_house.abs_pos),
        (6, natal_subject.sixth_house.abs_pos),
        (7, natal_subject.seventh_house.abs_pos),
        (8, natal_subject.eighth_house.abs_pos),
        (9, natal_subject.ninth_house.abs_pos),
        (10, natal_subject.tenth_house.abs_pos),
        (11, natal_subject.eleventh_house.abs_pos),
        (12, natal_subject.twelfth_house.abs_pos),
    ]


def find_house_for_degree(degree: float, cusps: list) -> int:
    for i in range(12):
        house_num, start = cusps[i]
        _, end = cusps[(i + 1) % 12]

        adjusted_degree = degree
        adjusted_end = end

        if adjusted_end < start:
            adjusted_end += 360

        if adjusted_degree < start:
            adjusted_degree += 360

        if start <= adjusted_degree < adjusted_end:
            return house_num

    return 1


def planet_line(label: str, planet, cusps: list) -> str:
    house = find_house_for_degree(planet.abs_pos, cusps)
    return f"{label}: в {sign_ru(planet.sign)}, попадает в {house} дом натальной карты"


def get_real_astrology(birth_date: str, birth_time: str, city: str) -> str:
    natal, city_data, time_unknown = create_subject_from_birth(
        birth_date,
        birth_time,
        city
    )

    note = ""
    if time_unknown:
        note = "\n⚠️ Время рождения неизвестно, поэтому дома и Асцендент рассчитаны условно на 12:00.\n"

    return f"""
📍 Город найден: {city_data["name"]}
🌐 Координаты: {city_data["lat"]}, {city_data["lng"]}
🕰 Часовой пояс: {city_data["timezone"]}
{note}
☀️ Солнце: в {sign_ru(natal.sun.sign)}
🌙 Луна: в {sign_ru(natal.moon.sign)}
⬆️ Асцендент: в {sign_ru(natal.first_house.sign)}
🧠 Меркурий: в {sign_ru(natal.mercury.sign)}
💖 Венера: в {sign_ru(natal.venus.sign)}
🔥 Марс: в {sign_ru(natal.mars.sign)}
"""


def get_today_transits(birth_date: str, birth_time: str, city: str) -> str:
    natal, city_data, time_unknown = create_subject_from_birth(
        birth_date,
        birth_time,
        city
    )

    today, now = create_subject_for_today(city_data)
    cusps = get_house_cusps(natal)

    note = ""
    if time_unknown:
        note = "\n⚠️ Время рождения неизвестно, поэтому дома рассчитаны условно на 12:00.\n"

    return f"""
📅 Дата расчета: {now.strftime("%d.%m.%Y %H:%M")}
📍 Локация расчета: {city_data["name"]}
{note}
Транзиты сегодняшнего дня по домам натальной карты:

☀️ {planet_line("Солнце сегодня", today.sun, cusps)}
🌙 {planet_line("Луна сегодня", today.moon, cusps)}
🧠 {planet_line("Меркурий сегодня", today.mercury, cusps)}
💖 {planet_line("Венера сегодня", today.venus, cusps)}
🔥 {planet_line("Марс сегодня", today.mars, cusps)}
🪐 {planet_line("Сатурн сегодня", today.saturn, cusps)}
"""


def get_astro_profile(birth_date: str, birth_time: str, city: str) -> str:
    real_astro = get_real_astrology(birth_date, birth_time, city)

    prompt = f"""
Ты современный астролог.

Данные пользователя:
Дата рождения: {birth_date}
Время рождения: {birth_time}
Город рождения: {city}

Реальные астрологические данные:
{real_astro}

Сделай краткий астропрофиль человека.

Используй HTML-разметку Telegram.
Разрешено использовать только тег <b>.
Не используй Markdown: не пиши **жирный текст**.

Структура строго такая:

✨ <b>Твой астропрофиль:</b>

🪐 <b>Основные положения:</b>
☀️ <b>Солнце в ...:</b> одна короткая фраза.
🌙 <b>Луна в ...:</b> одна короткая фраза.
⬆️ <b>Асцендент в ...:</b> одна короткая фраза.
🧠 <b>Меркурий в ...:</b> одна короткая фраза.
💖 <b>Венера в ...:</b> одна короткая фраза.
🔥 <b>Марс в ...:</b> одна короткая фраза.

🌞 <b>Основная энергия:</b>
🌙 <b>Эмоции и внутренний мир:</b>
⬆️ <b>Как ты проявляешься:</b>
🔥 <b>Сильные стороны:</b>
🪐 <b>На что стоит обратить внимание:</b>

Не делай прогноз на сегодня.
Не давай совет дня.
Не добавляй пункт "Не упусти возможность".
Пиши тепло, современно, понятно.
Не слишком длинно.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def get_daily_forecast(birth_date: str, birth_time: str, city: str) -> str:
    real_astro = get_real_astrology(birth_date, birth_time, city)
    today_transits = get_today_transits(birth_date, birth_time, city)

    prompt = f"""
Ты современный астролог и автор Telegram-гороскопов.

Данные пользователя:
Дата рождения: {birth_date}
Время рождения: {birth_time}
Город рождения: {city}

Натальная карта:
{real_astro}

Реальные транзиты на сегодня:
{today_transits}

Сделай персональный прогноз на сегодня.
Главная логика прогноза должна идти именно от сегодняшних транзитов:
например, Марс сегодня попадает в 10 дом, Венера в 2 дом, Луна в 7 дом и т.д.

Обязательно упомяни 2 конкретных факта из транзитов сегодняшнего дня.
Например:
"Марс сегодня активирует твой 10 дом..."
"Луна сегодня попадает в 7 дом..."
"Венера сегодня проходит через 2 дом..."

Используй HTML-разметку Telegram.
Разрешено использовать только тег <b>.
Не используй Markdown: не пиши **жирный текст**.

Структура строго такая:

✨ <b>Прогноз на сегодня:</b>
🌙 <b>Вайб дня:</b>
💘 <b>Любовь:</b>
💰 <b>Деньги и работа:</b>
🧘 <b>Совет дня:</b>
🍀 <b>Не упусти возможность:</b>
🚫 <b>Чего избегать:</b>

Не добавляй пункт "Что сейчас влияет".
Не добавляй пункт "Энергия".
Не используй фатальные предсказания.
Не давай медицинских, юридических или инвестиционных советов.
Пиши тепло, красиво, конкретно.
Не слишком длинно.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content