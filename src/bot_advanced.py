# bot.py

import os
import tempfile
import subprocess
from dotenv import load_dotenv
import telebot
import whisper
from transformers import pipeline

# ─── Загрузка настроек ───────────────────────────────────────────────────
load_dotenv()
TG_TOKEN = os.getenv("TG_TOKEN", "").strip()
assert TG_TOKEN, "Не задан TG_TOKEN в .env"

bot = telebot.TeleBot(TG_TOKEN)

# ─── Модели ──────────────────────────────────────────────────────────────
# оффлайн Whisper (официальный)
whisper_model = whisper.load_model("small")
# HF-суммаризатор
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


# ─── OGG→WAV (использует системный ffmpeg из PATH)────────────────────────
def ogg_to_wav(src_path: str) -> str:
    dst_path = src_path.replace(".ogg", ".wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", src_path, "-ar", "16000", dst_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return dst_path


# ─── /start ──────────────────────────────────────────────────────────────
@bot.message_handler(commands=["start"])
def handle_start(msg):
    bot.reply_to(msg, "👋 Hello! Send me a voice note, and I'll summarize it.")


# ─── Voice handler ───────────────────────────────────────────────────────
@bot.message_handler(content_types=["voice"])
def handle_voice(msg):
    # 1) Скачиваем OGG
    f_info = bot.get_file(msg.voice.file_id)
    raw = bot.download_file(f_info.file_path)
    ogg_tmp = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False).name
    with open(ogg_tmp, "wb") as f:
        f.write(raw)

    try:
        # 2) Конвертируем в WAV
        wav_tmp = ogg_to_wav(ogg_tmp)

        # 3) Транскрибируем Whisper
        text = whisper_model.transcribe(wav_tmp)["text"]

        # 4) Суммируем текст
        summary = summarizer(text, max_length=60, min_length=20, do_sample=False)[0][
            "summary_text"
        ]

        # 5) Отвечаем в чат
        bot.send_message(msg.chat.id, f"*TL;DR:*\n{summary}", parse_mode="Markdown")

    except Exception as e:
        print("Error in processing:", e)
        bot.send_message(msg.chat.id, "⚠️ Something went wrong.")

    finally:
        # 6) Удаляем temp-файлы
        for p in (ogg_tmp, locals().get("wav_tmp")):
            try:
                os.remove(p)
            except:
                pass


# ─── Запуск ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Bot is polling…")
    bot.infinity_polling()
