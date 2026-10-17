# Vacancy Application Bot

[English](README.md) | [Русский](README.ru.md)

A Telegram bot for collecting job applications. Applicants complete a guided form, review their details, and submit their application to a configured administrator.

## Features

- Step-by-step application form using aiogram FSM
- Fields: full name, age, city, job category, experience, introduction, phone number, and photo
- Cancel and restart controls
- Input validation and HTML escaping for user-supplied content
- Photo and application details delivered to the administrator
- Application state retained when Telegram delivery fails, allowing a retry
- Unit tests and GitHub Actions CI

**Interface language:** Russian. The English README documents the project for international reviewers; it does not translate the bot interface.

## Requirements

- Python 3.10 or later
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your numeric Telegram user ID (administrator)
- Dependencies from `requirements.txt`

## Local setup

```bash
git clone https://github.com/parviz-rahmonov/Vacancy-Application-Bot.git
cd Vacancy-Application-Bot
python -m venv .venv
```

Activate the environment:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure:

```dotenv
BOT_TOKEN=your_bot_token
ADMIN_ID=123456789
```

Never commit `.env` or share a real token.

Run the bot:

```bash
python main.py
```

The administrator must start a conversation with the bot before the bot can send them messages.

## Running tests

```bash
python -m unittest discover -s tests -v
```

GitHub Actions is configured in `.github/workflows/tests.yml` to run tests on pushes and pull requests. Passing tests do not guarantee that the live Telegram integration works.

## Repository structure

```text
.
├── main.py                    # Bot handlers, form states, keyboards
├── config.py                  # Environment-based settings validation
├── requirements.txt
├── .env.example
├── .gitignore
├── tests/
│   └── test_application.py
└── .github/workflows/
    └── tests.yml
```

## Workflow

1. Applicant sends `/start` and chooses to apply.
2. The bot collects and validates the form fields.
3. Applicant attaches a photo and reviews the summary.
4. On confirmation, the bot sends the photo and application details to the administrator.
5. If delivery fails, the form remains available for retry.

## Current limitations

- `MemoryStorage` is used: unfinished applications disappear when the process restarts.
- Phone validation currently targets Russian `+7` numbers (or `8`-prefixed 11-digit input).
- There is no database, applicant dashboard, or automatic duplicate-delivery prevention.
- If the photo reaches the administrator but the text delivery fails, retrying may send the photo again.
- The bot is intended for private chats.

## Security and privacy

Applications contain personal information (including phone numbers and photos). Protect administrator access, limit data retention, and obtain appropriate consent before collecting or processing applicant data. Do not log or commit applicant data or credentials.

## License

No license file is currently included. Usage and redistribution rights are not granted by default.
