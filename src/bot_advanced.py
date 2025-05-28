# bot.py

import os
import tempfile
import subprocess
import logging

from dotenv import load_dotenv
import telebot
import whisper
from summa.summarizer import summarize as summa_summarize

# ─── 1. Загрузка настроек и логгирование ────────────────────────────────
load_dotenv()
TG_TOKEN = os.getenv("TG_TOKEN", "").strip()
assert TG_TOKEN, "Заполните TG_TOKEN в файле .env"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s | %(message)s"
)
logging.info("Запуск бота…")

bot = telebot.TeleBot(TG_TOKEN)

# ─── 2. Whisper-модель для распознавания речи ────────────────────────────
whisper_model = whisper.load_model("small")

# ─── 3. Параметры ────────────────────────────────────────────────────────
FULL_TEXT_THRESHOLD = 5  # ≤5 с — полный транскрипт
MAX_DURATION = 20 * 60  # макс. длительность в секундах (20 мин)
SUMMARY_RATIO = 0.2  # брать 20% самых важных предложений


# ─── 4. Утилиты ─────────────────────────────────────────────────────────
def convert_to_wav(src_path: str) -> str:
    """
    Конвертирует любой аудиофайл (.ogg, .mp3 и т.д.)
    в WAV 16 kHz через системный ffmpeg.
    """
    dst = src_path.rsplit(".", 1)[0] + ".wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", src_path, "-ar", "16000", dst],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return dst


def make_summary(text: str) -> str:
    """
    Extractive TextRank-конспект через summa: выбирает наиболее важные
    предложения, сжимая текст до SUMMARY_RATIO.
    """
    clean = " ".join(text.replace("\n", " ").split()).strip()
    try:
        sents = summa_summarize(clean, ratio=SUMMARY_RATIO, split=True)
        if not sents:
            return clean
        return "\n".join(sents)
    except Exception:
        logging.exception("Ошибка summa_summarize")
        return clean


# ─── 5. Команды /start и /help ───────────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.reply_to(
        msg,
        "👋 Привет! Пришли мне голосовое (OGG) или аудиофайл (MP3) до 20 мин, "
        "я верну транскрипт или конспект.",
    )


@bot.message_handler(commands=["help"])
def cmd_help(msg):
    bot.send_message(
        msg.chat.id,
        "/start — запустить бота\n"
        "/help  — показать эту подсказку\n\n"
        "Отправь аудио:\n"
        f"• ≤{FULL_TEXT_THRESHOLD}s — полный транскрипт\n"
        f"• >{FULL_TEXT_THRESHOLD}s — конспект (~{int(SUMMARY_RATIO*100)}%)\n"
        f"• Макс. длительность: {MAX_DURATION//60} мин",
    )


# ─── 6. Обработчик голосовых и аудио файлов ───────────────────────────────
@bot.message_handler(content_types=["voice", "audio"])
def handle_audio(msg):
    # 1) Определяем file_id и длительность
    if msg.content_type == "voice":
        file_id, duration = msg.voice.file_id, msg.voice.duration
    else:
        file_id, duration = msg.audio.file_id, msg.audio.duration or 0

    logging.info("Получено %s, длительность %d с", msg.content_type, duration)

    # 2) Проверяем ограничение по длительности
    if duration > MAX_DURATION:
        bot.send_message(
            msg.chat.id, f"⚠️ Максимальная длительность — {MAX_DURATION//60} мин."
        )
        return

    # 3) Скачиваем исходный файл
    info = bot.get_file(file_id)
    raw = bot.download_file(info.file_path)
    ext = os.path.splitext(info.file_path)[1] or ".ogg"
    src = tempfile.NamedTemporaryFile(suffix=ext, delete=False).name
    with open(src, "wb") as f:
        f.write(raw)

    try:
        # 4) Конвертируем в WAV
        wav = convert_to_wav(src)

        # 5) Расшифровываем через Whisper
        text = whisper_model.transcribe(wav)["text"].strip()
        logging.info("Транскрипт: %.50s…", text)

        # 6) Формируем ответ
        if duration <= FULL_TEXT_THRESHOLD:
            response = f"*Transcript:*\n{text}"
        else:
            summary = make_summary(text)
            response = f"*Конспект:*\n{summary}"

        # 7) Отправляем пользователю
        bot.send_message(msg.chat.id, response, parse_mode="Markdown")

    except Exception:
        logging.exception("Ошибка при обработке аудио")
        bot.send_message(msg.chat.id, "⚠️ Произошла ошибка при обработке аудио.")
    finally:
        # 8) Удаляем временные файлы
        for p in (src, locals().get("wav")):
            if p and os.path.exists(p):
                os.remove(p)


# ─── 7. Запуск polling ───────────────────────────────────────────────────
if __name__ == "__main__":
    logging.info("Телеграм-бот запущен, начинаю polling…")
    bot.infinity_polling()
