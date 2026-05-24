import asyncio
import os
from datetime import datetime, date

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

from astro import get_astro_profile, get_daily_forecast
from database import create_tables, save_user, get_user, save_forecast, get_forecast


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

active_forecast_requests = set()

class BirthForm(StatesGroup):
    waiting_for_birth_date = State()
    waiting_for_birth_time = State()
    waiting_for_birth_city = State()


def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Получить прогноз на сегодня ✨")],
            [KeyboardButton(text="Мой астропрофиль 🌙")],
            [KeyboardButton(text="Изменить данные")]
        ],
        resize_keyboard=True
    )


def start_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Что умеет бот?")]
        ],
        resize_keyboard=True
    )


def is_valid_birth_date(text: str) -> bool:
    try:
        datetime.strptime(text, "%d.%m.%Y")
        return True
    except ValueError:
        return False


def is_valid_birth_time(text: str) -> bool:
    if text.lower() in ["не знаю", "не знаю.", "нет"]:
        return True

    try:
        datetime.strptime(text, "%H:%M")
        return True
    except ValueError:
        return False


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)

    if user:
        birth_date, birth_time, birth_city, astro_profile = user

        if not astro_profile:
            astro_profile = await get_astro_profile(
                birth_date,
                birth_time,
                birth_city
            )

            save_user(
                message.from_user.id,
                birth_date,
                birth_time,
                birth_city,
                astro_profile
            )

        await message.answer(
            f"С возвращением ✨\n\n{astro_profile}",
            reply_markup=main_keyboard()
        )
        return

    await state.set_state(BirthForm.waiting_for_birth_date)

    await message.answer(
        "Привет ✨ Я MyCosmosToday.\n\n"
        "Я составляю персональный прогноз на основе твоей натальной карты "
        "и реального положения планет ✨\n\n"
        "Чтобы начать, введи дату рождения в формате ДД.ММ.ГГГГ.\n\n"
        "Например:\n"
        "15.08.1998"
    )

@dp.message(F.text == "Что умеет бот?")
async def about(message: Message):
    await message.answer(
        "Я рассчитываю персональный прогноз "
        "по дате, времени и месту рождения ✨"
    )


@dp.message(F.text == "Узнать мой день ✨")
async def ask_birth_date(message: Message, state: FSMContext):
    await state.set_state(BirthForm.waiting_for_birth_date)

    await message.answer(
        "Супер ✨\n\n"
        "Введи дату рождения в формате ДД.ММ.ГГГГ\n\n"
        "Например:\n"
        "15.08.1998"
    )


@dp.message(BirthForm.waiting_for_birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    birth_date = message.text.strip()

    if not is_valid_birth_date(birth_date):
        await message.answer(
            "Кажется, дата введена не в том формате ✨\n\n"
            "Пожалуйста, введи дату рождения так:\n"
            "ДД.ММ.ГГГГ\n\n"
            "Например:\n"
            "15.08.1998"
        )
        return

    await state.update_data(birth_date=birth_date)
    await state.set_state(BirthForm.waiting_for_birth_time)

    await message.answer(
        "Теперь введи время рождения ⏰\n\n"
        "Например:\n"
        "14:35\n\n"
        "Если не знаешь — напиши:\n"
        "не знаю"
    )


@dp.message(BirthForm.waiting_for_birth_time)
async def process_birth_time(message: Message, state: FSMContext):
    birth_time = message.text.strip()

    if not is_valid_birth_time(birth_time):
        await message.answer(
            "Кажется, время введено не в том формате ✨\n\n"
            "Пожалуйста, введи время так:\n"
            "14:35\n\n"
            "Если не знаешь точное время — напиши:\n"
            "не знаю"
        )
        return

    await state.update_data(birth_time=birth_time)
    await state.set_state(BirthForm.waiting_for_birth_city)

    await message.answer(
        "Теперь введи город рождения 🌍\n\n"
        "Например:\n"
        "Москва"
    )


@dp.message(BirthForm.waiting_for_birth_city)
async def process_birth_city(message: Message, state: FSMContext):
    birth_city = message.text.strip()
    data = await state.get_data()

    birth_date = data.get("birth_date")
    birth_time = data.get("birth_time")

    try:
        astro_profile = await get_astro_profile(
            birth_date,
            birth_time,
            birth_city
        )
    except Exception:
        await message.answer(
            "Не удалось обработать данные ✨\n\n"
            "Проверь, пожалуйста, город рождения "
            "и попробуй еще раз."
        )
        return

    save_user(
        message.from_user.id,
        birth_date,
        birth_time,
        birth_city,
        astro_profile
    )

    await message.answer(
        f"✨ Твои данные сохранены!\n\n"
        f"Дата рождения: {birth_date}\n"
        f"Время рождения: {birth_time}\n"
        f"Город рождения: {birth_city}\n\n"
        f"{astro_profile}",
        reply_markup=main_keyboard()
    )

    await state.clear()


@dp.message(F.text == "Получить прогноз на сегодня ✨")
async def daily_forecast(message: Message):
    user = get_user(message.from_user.id)

    if not user:
        await message.answer(
            "Я пока не знаю твоих данных рождения ✨\n\n"
            "Нажми «Узнать мой день ✨», чтобы начать."
        )
        return

    birth_date, birth_time, birth_city, astro_profile = user
    today = date.today().isoformat()

    saved_forecast = get_forecast(
        message.from_user.id,
        today,
        birth_date,
        birth_time,
        birth_city
    )

    if saved_forecast:
        await message.answer(saved_forecast)
        return

    user_id = message.from_user.id

    if user_id in active_forecast_requests:
        await message.answer(
            "Я уже формирую твой прогноз ✨\n\n"
            "Подожди немного, скоро он будет готов."
        )
        return

    active_forecast_requests.add(user_id)

    try:
        await message.answer("✨ Анализирую положение планет...")
        await asyncio.sleep(2)

        await message.answer("🌙 Считываю энергетику дня...")
        await asyncio.sleep(2)

        await message.answer("🪐 Формирую твой прогноз...")
        await asyncio.sleep(2)

        forecast = await get_daily_forecast(
            birth_date,
            birth_time,
            birth_city
        )

        save_forecast(
            message.from_user.id,
            today,
            birth_date,
            birth_time,
            birth_city,
            forecast
        )

        await message.answer(forecast)

    except Exception as e:
        print(e)
        await message.answer(f"Ошибка:\n{e}")

    finally:
        active_forecast_requests.discard(user_id)

    await message.answer("✨ Анализирую положение планет...")
    await asyncio.sleep(2)

    await message.answer("🌙 Считываю энергетику дня...")
    await asyncio.sleep(2)

    await message.answer("🪐 Формирую твой прогноз...")
    await asyncio.sleep(2)

    try:
        forecast = await get_daily_forecast(
            birth_date,
            birth_time,
            birth_city
        )
    except Exception as e:
        print(e)
        await message.answer(f"Ошибка:\n{e}")
        return

    save_forecast(
        message.from_user.id,
        today,
        birth_date,
        birth_time,
        birth_city,
        forecast
    )

    await message.answer(forecast)


@dp.message(F.text == "Изменить данные")
async def change_data(message: Message, state: FSMContext):
    await state.set_state(BirthForm.waiting_for_birth_date)

    await message.answer(
        "Хорошо ✨\n\n"
        "Введи новую дату рождения в формате ДД.ММ.ГГГГ.\n\n"
        "Например:\n"
        "15.08.1998"
    )


@dp.message(F.text == "Мой астропрофиль 🌙")
async def show_astro_profile(message: Message):
    user = get_user(message.from_user.id)

    if not user:
        await message.answer(
            "Я пока не знаю твоих данных рождения ✨\n\n"
            "Нажми «Узнать мой день ✨», чтобы начать."
        )
        return

    birth_date, birth_time, birth_city, astro_profile = user

    if not astro_profile:
        await message.answer("🌙 Рассчитываю твой астропрофиль...")

        try:
            astro_profile = await get_astro_profile(
                birth_date,
                birth_time,
                birth_city
            )
        except Exception:
            await message.answer(
                "Не удалось показать астропрофиль ✨\n\n"
                "Попробуй, пожалуйста, изменить данные рождения."
            )
            return

        save_user(
            message.from_user.id,
            birth_date,
            birth_time,
            birth_city,
            astro_profile
        )

    await message.answer(astro_profile)


async def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден")

    create_tables()
    print("Бот запущен 🚀")

    #asyncio.create_task(daily_reminder())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())