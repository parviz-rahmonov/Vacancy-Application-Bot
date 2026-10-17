from config import BOT_TOKEN, ADMIN_ID
import asyncio
import html
import logging
import sys
from typing import Any

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

# ---------------------------------------------------------------------------
# Конфигурация
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Направления
# ---------------------------------------------------------------------------

DIRECTIONS = [
    ("🏥 Медицина",         "direction_medicine"),
    ("💻 Программирование", "direction_programming"),
    ("🚕 Такси",            "direction_taxi"),
    ("🛵 Курьер",           "direction_courier"),
    ("📦 Доставка",         "direction_delivery"),
    ("📚 Учитель",          "direction_teacher"),
]

# ---------------------------------------------------------------------------
# Тексты кнопок ReplyKeyboard
# ---------------------------------------------------------------------------

BTN_CANCEL  = "❌ Отмена"
BTN_RESTART = "🔄 Начать заново"

# ---------------------------------------------------------------------------
# Клавиатуры
# ---------------------------------------------------------------------------

def start_keyboard() -> InlineKeyboardMarkup:
    """Inline-кнопка на приветственном сообщении."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Заполнить анкету", callback_data="start_form")],
        ]
    )


def form_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Постоянная клавиатура снизу — видна на всех шагах анкеты.
    persistent=True — клавиатура НЕ сворачивается когда пользователь печатает.
    Появилось в Telegram Bot API 6.2, aiogram 3.x поддерживает.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_CANCEL),
                KeyboardButton(text=BTN_RESTART),
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        persistent=True,                      # ← ключевой параметр
        input_field_placeholder="Введите ответ…",
    )


def remove_reply_keyboard() -> ReplyKeyboardRemove:
    """Убирает ReplyKeyboard когда анкета завершена или отменена."""
    return ReplyKeyboardRemove()


def directions_keyboard() -> InlineKeyboardMarkup:
    """Inline-кнопки выбора направления внутри сообщения."""
    rows = [
        [InlineKeyboardButton(text=label, callback_data=cb)]
        for label, cb in DIRECTIONS
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_keyboard() -> InlineKeyboardMarkup:
    """Inline-кнопка подтверждения — внутри сообщения с фото."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Отправить заявку", callback_data="confirm_yes")],
        ]
    )

# ---------------------------------------------------------------------------
# FSM состояния
# ---------------------------------------------------------------------------

class ApplicationForm(StatesGroup):
    full_name  = State()
    age        = State()
    city       = State()
    direction  = State()
    experience = State()
    about      = State()
    phone      = State()
    photo      = State()
    confirm    = State()

# ---------------------------------------------------------------------------
# Хелперы
# ---------------------------------------------------------------------------

def build_summary(data: dict[str, Any]) -> str:
    return (
        "📋 <b>Ваша заявка:</b>\n\n"
        f"👤 <b>ФИО:</b> {html.escape(str(data.get('full_name', '—')))}\n"
        f"🎂 <b>Возраст:</b> {html.escape(str(data.get('age', '—')))}\n"
        f"🏙 <b>Город:</b> {html.escape(str(data.get('city', '—')))}\n"
        f"🎯 <b>Направление:</b> {html.escape(str(data.get('direction', '—')))}\n"
        f"🗂 <b>Опыт работы:</b>\n{html.escape(str(data.get('experience', '—')))}\n\n"
        f"📝 <b>О себе:</b>\n{html.escape(str(data.get('about', '—')))}\n\n"
        f"📞 <b>Телефон:</b> {html.escape(str(data.get('phone', '—')))}\n"
        f"🖼 <b>Фото:</b> {'прикреплено' if data.get('photo_file_id') else '—'}"
    )

# ---------------------------------------------------------------------------
# Роутер
# ---------------------------------------------------------------------------

router = Router()

# ---------------------------------------------------------------------------
# Глобальные перехватчики ReplyKeyboard — ВЫШЕ всех FSM-хендлеров
# Срабатывают в любом состоянии анкеты
# ---------------------------------------------------------------------------

@router.message(F.text == BTN_CANCEL)
async def global_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "❌ <b>Анкета отменена.</b>\n\nЕсли захотите вернуться — нажмите /start",
        parse_mode=ParseMode.HTML,
        reply_markup=remove_reply_keyboard(),
    )


@router.message(F.text == BTN_RESTART)
async def global_restart(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "🔄 <b>Анкета сброшена!</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=remove_reply_keyboard(),
    )
    await message.answer(
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Это бот для подачи заявки на вакансию.\n"
        "Нажмите кнопку ниже, чтобы начать 👇",
        parse_mode=ParseMode.HTML,
        reply_markup=start_keyboard(),
    )

# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Это бот для подачи заявки на вакансию.\n"
        "Нажмите кнопку ниже, чтобы начать 👇",
        parse_mode=ParseMode.HTML,
        reply_markup=start_keyboard(),
    )


@router.callback_query(F.data == "start_form")
async def cb_start_form(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(
        "📋 <b>Начинаем заполнение анкеты!</b>\n\n"
        "Введите ваше <b>полное имя (ФИО)</b>:",
        parse_mode=ParseMode.HTML,
        reply_markup=form_reply_keyboard(),  # ← первый показ ReplyKeyboard
    )
    await state.set_state(ApplicationForm.full_name)
    await callback.answer()

# ---------------------------------------------------------------------------
# Шаги анкеты
# ВАЖНО: reply_markup=form_reply_keyboard() передаём в КАЖДЫЙ answer().
# Это гарантирует, что Telegram не уберёт клавиатуру ни на одном шаге.
# Повторная передача той же ReplyKeyboard не вызывает мигания —
# Telegram просто игнорирует дублирующий апдейт клавиатуры.
# ---------------------------------------------------------------------------

@router.message(ApplicationForm.full_name)
async def process_full_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not (2 <= len(name) <= 120):
        await message.answer(
            "⚠️ Введите корректное ФИО (минимум 2 символа).",
            reply_markup=form_reply_keyboard(),
        )
        return
    await state.update_data(full_name=name)
    await message.answer(
        "✅ Принято!\n\nТеперь укажите ваш <b>возраст</b> (число):",
        parse_mode=ParseMode.HTML,
        reply_markup=form_reply_keyboard(),
    )
    await state.set_state(ApplicationForm.age)


@router.message(ApplicationForm.age)
async def process_age(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not (text.isascii() and text.isdecimal() and len(text) <= 2 and 14 <= int(text) <= 80):
        await message.answer(
            "⚠️ Введите корректный возраст (от 14 до 80 лет).",
            reply_markup=form_reply_keyboard(),
        )
        return
    await state.update_data(age=text)
    await message.answer(
        "✅ Принято!\n\nИз какого вы <b>города</b>?",
        parse_mode=ParseMode.HTML,
        reply_markup=form_reply_keyboard(),
    )
    await state.set_state(ApplicationForm.city)


@router.message(ApplicationForm.city)
async def process_city(message: Message, state: FSMContext) -> None:
    city = (message.text or "").strip()
    if not (2 <= len(city) <= 100):
        await message.answer(
            "⚠️ Введите корректное название города.",
            reply_markup=form_reply_keyboard(),
        )
        return
    await state.update_data(city=city)
    # InlineKeyboard направлений + ReplyKeyboard снизу — не конфликтуют
    await message.answer(
        "✅ Принято!\n\n🎯 Выберите <b>направление</b>, которое вас интересует:",
        parse_mode=ParseMode.HTML,
        reply_markup=directions_keyboard(),  # ← Inline для выбора направления
        # ReplyKeyboard уже висит снизу — она не сбрасывается при отправке Inline
    )
    await state.set_state(ApplicationForm.direction)


@router.callback_query(ApplicationForm.direction, F.data.startswith("direction_"))
async def process_direction(callback: CallbackQuery, state: FSMContext) -> None:
    direction_label = next((label for label, cb in DIRECTIONS if cb == callback.data), None)
    if direction_label is None:
        await callback.answer("Выберите направление из списка.", show_alert=True)
        return
    await state.update_data(direction=direction_label)
    # edit_text не влияет на ReplyKeyboard — она остаётся
    await callback.message.edit_text(
        f"✅ Вы выбрали: <b>{direction_label}</b>\n\n"
        f"Расскажите о вашем <b>опыте работы</b>:\n"
        f"<i>(Компании, должности, годы — в свободной форме)</i>",
        parse_mode=ParseMode.HTML,
    )
    # Отдельным answer явно «прибиваем» ReplyKeyboard, на случай если
    # после edit_text на каком-то клиенте она слетела
    await callback.message.answer(
        "⌨️ Напишите ваш опыт работы:",
        reply_markup=form_reply_keyboard(),
    )
    await state.set_state(ApplicationForm.experience)
    await callback.answer()


@router.message(ApplicationForm.direction)
async def process_direction_wrong(message: Message) -> None:
    await message.answer(
        "👆 Пожалуйста, выберите направление нажав на одну из кнопок выше.",
        reply_markup=form_reply_keyboard(),
    )


@router.message(ApplicationForm.experience)
async def process_experience(message: Message, state: FSMContext) -> None:
    exp = (message.text or "").strip()
    if not (5 <= len(exp) <= 1200):
        await message.answer(
            "⚠️ Опишите ваш опыт подробнее (минимум 5 символов).",
            reply_markup=form_reply_keyboard(),
        )
        return
    await state.update_data(experience=exp)
    await message.answer(
        "✅ Принято!\n\nРасскажите немного <b>о себе</b> — почему хотите работать у нас, "
        "ваши сильные стороны:",
        parse_mode=ParseMode.HTML,
        reply_markup=form_reply_keyboard(),
    )
    await state.set_state(ApplicationForm.about)


@router.message(ApplicationForm.about)
async def process_about(message: Message, state: FSMContext) -> None:
    about = (message.text or "").strip()
    if not (10 <= len(about) <= 1200):
        await message.answer(
            "⚠️ Напишите немного больше о себе (минимум 10 символов).",
            reply_markup=form_reply_keyboard(),
        )
        return
    await state.update_data(about=about)
    await message.answer(
        "✅ Принято!\n\nУкажите ваш <b>номер телефона</b>:\n"
        "<i>(Формат: +7XXXXXXXXXX или 8XXXXXXXXXX)</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=form_reply_keyboard(),
    )
    await state.set_state(ApplicationForm.phone)


@router.message(ApplicationForm.phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip().replace(" ", "").replace("-", "")
    normalized = phone
    if phone.startswith("8") and len(phone) == 11:
        normalized = "+7" + phone[1:]
    if not (normalized.startswith("+7") and len(normalized) == 12 and normalized[1:].isascii() and normalized[1:].isdecimal()):
        await message.answer(
            "⚠️ Номер введён некорректно.\n"
            "Попробуйте ещё раз в формате <b>+7XXXXXXXXXX</b>.",
            parse_mode=ParseMode.HTML,
            reply_markup=form_reply_keyboard(),
        )
        return
    await state.update_data(phone=normalized)
    await message.answer(
        "✅ Принято!\n\n📸 Теперь отправьте ваше <b>фото</b> (портретное, чёткое):",
        parse_mode=ParseMode.HTML,
        reply_markup=form_reply_keyboard(),
    )
    await state.set_state(ApplicationForm.photo)


@router.message(ApplicationForm.photo, F.photo)
async def process_photo(message: Message, state: FSMContext) -> None:
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_file_id)
    data = await state.get_data()
    # Show the photo and full summary separately to avoid the 1024-char caption limit.
    await message.answer_photo(
        photo=photo_file_id,
        reply_markup=form_reply_keyboard(),
    )
    await message.answer(
        build_summary(data) + "\n\n<b>Всё верно? Отправляем заявку?</b>",
        parse_mode=ParseMode.HTML,
    )
    # Inline confirm отправляем отдельным сообщением чтобы не конфликтовать
    await message.answer(
        "👇 Нажмите кнопку для отправки:",
        reply_markup=confirm_keyboard(),
    )
    await state.set_state(ApplicationForm.confirm)


@router.message(ApplicationForm.photo)
async def process_photo_wrong(message: Message) -> None:
    await message.answer(
        "⚠️ Пожалуйста, отправьте именно <b>фотографию</b>, а не файл или текст.",
        parse_mode=ParseMode.HTML,
        reply_markup=form_reply_keyboard(),
    )


# ---------------------------------------------------------------------------
# Подтверждение
# ---------------------------------------------------------------------------

@router.callback_query(ApplicationForm.confirm, F.data == "confirm_yes")
async def confirm_yes(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    photo_id = data.get("photo_file_id")
    if not photo_id:
        await callback.answer("Фото не найдено. Начните анкету заново.", show_alert=True)
        return

    user = callback.from_user
    user_link = f'<a href="tg://user?id={user.id}">{html.escape(user.full_name)}</a>'
    username = html.escape(user.username or "—")
    admin_text = (
        "🔔 <b>Новая заявка на вакансию!</b>\n\n"
        f"От: {user_link} (@{username}, ID: <code>{user.id}</code>)\n\n"
        + build_summary(data)
    )

    try:
        # Keep the application state until both messages have been delivered.
        # A separate text message avoids Telegram's 1024-character photo caption limit.
        await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id)
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception("Ошибка доставки заявки user_id=%s", user.id)
        await callback.answer("Не удалось отправить заявку. Повторите попытку.", show_alert=True)
        return

    await state.clear()
    await callback.answer("Заявка отправлена!")
    await callback.message.answer(
        "✅ <b>Заявка успешно отправлена!</b>\n\n"
        "Наш HR-специалист свяжется с вами в ближайшее время. Удачи! 🍀\n\n"
        "Чтобы подать новую заявку — нажмите /start",
        parse_mode=ParseMode.HTML,
        reply_markup=remove_reply_keyboard(),
    )
    try:
        await callback.message.delete()
    except Exception:
        logger.warning("Не удалось удалить сообщение подтверждения user_id=%s", user.id)
    logger.info("Заявка от user_id=%s отправлена администратору", user.id)


@router.message(ApplicationForm.confirm)
async def confirm_unexpected(message: Message) -> None:
    await message.answer(
        "👆 Пожалуйста, воспользуйтесь кнопкой выше для отправки заявки.",
        reply_markup=form_reply_keyboard(),
    )


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------

async def main() -> None:
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    logger.info("Бот запущен. Ожидаю сообщений...")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())