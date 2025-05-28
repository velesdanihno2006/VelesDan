import os
from dotenv import load_dotenv
import telebot

load_dotenv()
TOKEN = os.getenv("TG_TOKEN").strip()
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def on_start(msg):
    bot.reply_to(msg, "👋 Bot is alive! Send me a voice note to summarize.")


@bot.message_handler(content_types=["voice"])
def on_voice(msg):
    bot.reply_to(msg, "⏳ Got your voice, processing…")


if __name__ == "__main__":
    print("Polling…")
    bot.infinity_polling()
