# bot.py

import os
import tempfile
import subprocess
import logging

from dotenv import load_dotenv
import telebot
import whisper
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# ─── 1. Загрузка переменных и логгирование ───────────────────────────────
load_dotenv()
TG_TOKEN = os.getenv("TG_TOKEN", "").strip()
if not TG_TOKEN:
    raise RuntimeError("❌ В .env не найден TG_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s | %(message)s"
)
logging.info("Старт бота…")

# ─── 2. Инициализация Telegram-бота и Whisper ───────────────────────────
bot = telebot.TeleBot(TG_TOKEN)
whisper_model = whisper.load_model("small")

# ─── 3. Подключаем RuT5SumGazeta через safetensors ───────────────────────
MODEL_NAME = "IlyaGusev/rut5_base_sum_gazeta"
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME,
    use_safetensors=True
)
model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME,
    use_safetensors=True,
    trust_remote_code=False
)
summarizer = pipeline(
    "summarization",
    model=model,
    tokenizer=tokenizer,
    device=-1,            # CPU; для GPU укажите device=0
    framework="pt"
)

# ─── 4. Константы и режимы суммаризации ──────────────────────────────────
FULL_TEXT_THRESHOLD = 5       # ≤5 с — полный транскрипт
MAX_DURATION        = 20 * 60 # макс. длительность 20 мин
MAX_MESSAGE_LEN     = 4000    # лимит символов в Telegram

LENGTH_PARAMS = {
    "short":  (10,  64),
    "medium": (120, 384),
    "long":   (240, 768),
}
chat_length_mode = {}

# ─── 5. Утилиты ─────────────────────────────────────────────────────────
def convert_to_wav(src: str) -> str:
    dst = src.rsplit(".", 1)[0] + ".wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", src, "-ar", "16000", dst],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )
    return dst

def make_summary(text: str, mode: str) -> str:
    clean = " ".join(text.replace("\n", " ").split())
    min_len, max_len = LENGTH_PARAMS.get(mode, LENGTH_PARAMS["medium"])
    try:
        out = summarizer(
            clean,
            max_length=max_len,
            min_length=min_len,
            do_sample=False,
            truncation=True
        )
        return out[0]["summary_text"].strip()
    except Exception as e:
        logging.error("Ошибка суммаризации (%s): %s", mode, e)
        return clean

def chunk_message(text: str, limit: int = MAX_MESSAGE_LEN) -> list[str]:
    parts = []
    while len(text) > limit:
        idx = text.rfind("\n", 0, limit)
        if idx <= 0:
            idx = limit
        parts.append(text[:idx].strip())
        text = text[idx:].lstrip()
    if text:
        parts.append(text)
    return parts

# ─── 6. Команды выбора длины конспекта ───────────────────────────────────
@bot.message_handler(commands=["short"])
def cmd_short(m):
    chat_length_mode[m.chat.id] = "short"
    bot.reply_to(m, "Режим конспекта установлен: *короткий*.", parse_mode="Markdown")

@bot.message_handler(commands=["medium"])
def cmd_medium(m):
    chat_length_mode[m.chat.id] = "medium"
    bot.reply_to(m, "Режим конспекта установлен: *средний*.", parse_mode="Markdown")

@bot.message_handler(commands=["long"])
def cmd_long(m):
    chat_length_mode[m.chat.id] = "long"
    bot.reply_to(m, "Режим конспекта установлен: *длинный*.", parse_mode="Markdown")

# ─── 7. /start и /help ───────────────────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(m):
    chat_length_mode[m.chat.id] = "medium"
    bot.reply_to(
        m,
        "👋 Привет! Настрой длину конспекта:\n"
        "/short  — короткий\n"
        "/medium — средний (по умолчанию)\n"
        "/long   — длинный\n\n"
        "Затем отправь голосовое (OGG) или аудио (MP3) до 20 мин:\n"
        f"• ≤{FULL_TEXT_THRESHOLD}s — полный транскрипт\n"
        "• >5s — нейросетевой конспект"
    )

@bot.message_handler(commands=["help"])
def cmd_help(m):
    bot.send_message(
        m.chat.id,
        "Использование:\n"
        "/short  — короткий конспект\n"
        "/medium — средний конспект\n"
        "/long   — длинный конспект\n\n"
        "После выбора режима пришли голосовое/аудио до 20 мин:\n"
        f"• ≤{FULL_TEXT_THRESHOLD}s — полный текст\n"
        "• >5s — конспект"
    )

# ─── 8. Обработчик голосовых и аудиосообщений ───────────────────────────
@bot.message_handler(content_types=["voice", "audio"])
def handle_audio(m):
    if m.content_type == "voice":
        fid, dur = m.voice.file_id, m.voice.duration
    else:
        fid, dur = m.audio.file_id, m.audio.duration or 0

    logging.info("Получено %s длительностью %dс", m.content_type, dur)
    if dur > MAX_DURATION:
        return bot.send_message(m.chat.id, f"⚠️ Длина аудио ≤ {MAX_DURATION//60} мин.")

    info = bot.get_file(fid)
    raw  = bot.download_file(info.file_path)
    ext  = os.path.splitext(info.file_path)[1] or ".ogg"
    src  = tempfile.NamedTemporaryFile(suffix=ext, delete=False).name
    with open(src, "wb") as f:
        f.write(raw)

    try:
        wav = convert_to_wav(src)
        txt = whisper_model.transcribe(wav)["text"].strip()
        logging.info("Транскрипт: %.60s…", txt)

        if dur <= FULL_TEXT_THRESHOLD:
            parts = [f"*Transcript:*\n{txt}"]
        else:
            mode = chat_length_mode.get(m.chat.id, "medium")
            summary = make_summary(txt, mode)
            parts = chunk_message(f"*Summary ({mode}):*\n{summary}")

        for part in parts:
            bot.send_message(m.chat.id, part, parse_mode="Markdown")

    except Exception:
        logging.exception("Ошибка при обработке аудио")
        bot.send_message(m.chat.id, "⚠️ Ошибка при обработке аудио.")
    finally:
        for fn in (src, locals().get("wav")):
            if fn and os.path.exists(fn):
                os.remove(fn)

# ─── 9. Запуск polling ───────────────────────────────────────────────────
if __name__ == "__main__":
    logging.info("Бот запущен, начинаю polling…")
    bot.infinity_polling()
