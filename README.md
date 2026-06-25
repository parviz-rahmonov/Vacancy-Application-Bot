# 📋 Vacancy Application Bot

Telegram-бот для подачи заявки на вакансию. Пользователь проходит пошаговую анкету, результат отправляется администратору.

## 🚀 Быстрый старт

```bash
pip install aiogram==3.7.0
python main.py
```

В `main.py` укажи свои значения:
```python
BOT_TOKEN = "ваш токен от @BotFather"
ADMIN_ID  = ваш Telegram ID
```

---

## 🛠 Стек

| Компонент | Версия |
|-----------|--------|
| Python    | 3.10+  |
| aiogram   | 3.7.0  |
| FSM Storage | MemoryStorage (in-memory) |

---

## 🏗 Архитектура

```
main.py
│
├── Конфигурация
│   ├── BOT_TOKEN, ADMIN_ID
│   └── DIRECTIONS — список направлений вакансий
│
├── Клавиатуры
│   ├── start_keyboard()        — Inline «Заполнить анкету»
│   ├── form_reply_keyboard()   — ReplyKeyboard «Отмена / Начать заново»
│   │                             persistent=True → не скрывается при наборе
│   ├── directions_keyboard()   — Inline выбор направления
│   └── confirm_keyboard()      — Inline «Отправить заявку»
│
├── FSM — ApplicationForm (9 шагов)
│   ├── full_name   → возраст
│   ├── age         → город
│   ├── city        → направление (Inline)
│   ├── direction   → опыт работы
│   ├── experience  → о себе
│   ├── about       → телефон
│   ├── phone       → фото
│   ├── photo       → подтверждение
│   └── confirm     → отправка администратору
│
├── Глобальные хендлеры (приоритет выше FSM)
│   ├── BTN_CANCEL  — сброс состояния, выход из анкеты
│   └── BTN_RESTART — сброс + возврат на /start
│
└── Точка входа
    └── main() — polling, MemoryStorage, Router
```

---

## 👤 Роли

| Роль | Что может |
|------|-----------|
| **Пользователь** | Запускает `/start`, заполняет анкету, отменяет или перезапускает в любой момент |
| **Администратор** | Получает готовую заявку (фото + все данные) в личные сообщения |

---

## 📂 Структура проекта

```
.
└── main.py   # весь код в одном файле
```

---

## ⚠️ Примечания

- `MemoryStorage` — данные хранятся в памяти и сбрасываются при перезапуске бота. Для продакшена замените на `RedisStorage`.
- `persistent=True` в ReplyKeyboard требует Telegram Bot API 6.2+.
- Бот работает только в личных сообщениях (не в группах).
