
# Telegram Horoscope Bot (Python + pyTelegramBotAPI)

> **Предметная область:** боты  
> **Технология:** Telegram-боты на Python

---

## 1. Исследование и подготовка

| № | Действие | Что выясняем/получаем |
|---|----------|-----------------------|
| 1 | **Читаем статью freeCodeCamp** «How to Create a Telegram Bot Using Python». | Понимаем общую схему: BotFather → токен → библиотека → обработчики. |
| 2 | **Создаём бота у @BotFather**: `/newbot` → имя → username. | Получаем `BOT_TOKEN` – единственный ключ для доступа к Bot API. |
| 3 | **Устанавливаем библиотеку** `pyTelegramBotAPI`: <br>`pip install pyTelegramBotAPI`. | Выбираем её как самую простую для синхронного кода новичка. |
| 4 | **Готовим переменные окружения**: <br>создаём файл `.env` и записываем `BOT_TOKEN=…`. | Следуем совету статьи: хранить секрет отдельно от кода. |
| 5 | **Активируем переменные**: <br>`source .env`. | Токен попадает в окружение → читается через `os.environ`. |
| 6 | **Пишем минимальный `bot.py`** из статьи: <br>`TeleBot(token)`, обработчики `/start`, echo. | Проверяем, что бот отвечает в чате – базовая связка работает. |

> ![image](https://github.com/user-attachments/assets/1d8b47c9-f6f1-4f66-b159-28aef0840cf6)
 
> ![image](https://github.com/user-attachments/assets/9ae1496e-f892-4b40-be6e-c0e20001d61e)


---

## 2. Полное руководство для начинающих

### 2.1 Что понадобится
* Python ≥ 3.10  
* Аккаунт Telegram  
* Любой редактор кода

### 2.2 Проект и виртуальное окружение
```bash
git clone https://github.com/YOUR_USERNAME/telegram-horoscope-bot.git
cd telegram-horoscope-bot
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\Activate.ps1
pip install pyTelegramBotAPI python-dotenv requests
````

### 2.3 Файл `.env`

```env
BOT_TOKEN=123456789:AAH-Your-Secret-Token
```

и добавить `.env` в `.gitignore`.

### 2.4 Исходный код `bot.py`

```python
import os
import telebot
import requests
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
assert BOT_TOKEN, "BOT_TOKEN not found; check .env"

bot = telebot.TeleBot(BOT_TOKEN)

def get_daily_horoscope(sign: str, day: str) -> dict:
    url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
    return requests.get(url, params={"sign": sign, "day": day}).json()

def fetch_horoscope(message, sign):
    day = message.text.strip()
    data = get_daily_horoscope(sign, day)["data"]
    reply = (
        f"*Horoscope:* {data['horoscope_data']}\\n"
        f"*Sign:* {sign}\\n"
        f"*Day:* {data['date']}"
    )
    bot.send_message(message.chat.id, "Here's your horoscope!")
    bot.send_message(message.chat.id, reply, parse_mode="Markdown")

def day_handler(message):
    sign = message.text.strip()
    prompt = (
        "Which day?\n"
        "Enter *TODAY*, *TOMORROW*, *YESTERDAY*, "
        "or YYYY-MM-DD."
    )
    msg = bot.send_message(message.chat.id, prompt, parse_mode="Markdown")
    bot.register_next_step_handler(msg, fetch_horoscope, sign.capitalize())

@bot.message_handler(commands=["horoscope"])
def sign_handler(message):
    prompt = (
        "What's your zodiac sign?\n"
        "Choose one: *Aries*, *Taurus*, *Gemini*, *Cancer*, *Leo*, *Virgo*, "
        "*Libra*, *Scorpio*, *Sagittarius*, *Capricorn*, *Aquarius*, *Pisces*."
    )
    msg = bot.send_message(message.chat.id, prompt, parse_mode="Markdown")
    bot.register_next_step_handler(msg, day_handler)

if __name__ == "__main__":
    print("Bot is polling…")
    bot.infinity_polling()
```

### 2.5 Запуск

```bash
python bot.py
```

Пример. Отправьте боту `/horoscope` → `Aries` → `TODAY` — получите прогноз.

> ![image](https://github.com/user-attachments/assets/3ae25536-3016-49ea-ae24-d79a695bfe81)

---


## 4. Типовые ошибки

| Ошибка             | Причина             | Решение                              |
| ------------------ | ------------------- | ------------------------------------ |
| `assert BOT_TOKEN` | Токен не загрузился | проверить `.env`, `load_dotenv()`    |
| Бот молчит         | Privacy Mode        | `@BotFather → /setprivacy → Disable` |
| `ConnectionError`  | API недоступен      | попробовать позже                    |

---


