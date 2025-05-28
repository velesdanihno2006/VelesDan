import os
import telebot
import requests

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)


def get_daily_horoscope(sign: str, day: str) -> dict:
    url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
    params = {"sign": sign, "day": day}
    response = requests.get(url, params)
    return response.json()


def fetch_horoscope(message, sign):
    day = message.text
    horoscope = get_daily_horoscope(sign, day)
    data = horoscope["data"]

    # готовим итоговое сообщение
    horoscope_message = (
        f'*Гороскоп:* {data["horoscope_data"]}\\n'
        f"*Знак:* {sign}\\n"
        f'*Дата:* {data["date"]}'
    )

    bot.send_message(message.chat.id, "Ваш гороскоп:")
    bot.send_message(message.chat.id, horoscope_message, parse_mode="Markdown")


def day_handler(message):
    sign = message.text
    text = (
        "За какой день хотите узнать прогноз?\n"
        "Выберите: *TODAY* (сегодня), *TOMORROW* (завтра), *YESTERDAY* (вчера)\n"
        "или введите дату в формате YYYY-MM-DD."
    )
    sent_msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, fetch_horoscope, sign.capitalize())


@bot.message_handler(commands=["horoscope"])
def sign_handler(message):
    text = (
        "Какой у вас знак зодиака?\n"
        "Выберите: *Aries*, *Taurus*, *Gemini*, *Cancer*, *Leo*, *Virgo*, "
        "*Libra*, *Scorpio*, *Sagittarius*, *Capricorn*, *Aquarius*, *Pisces*."
    )
    sent_msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(sent_msg, day_handler)


bot.infinity_polling()
