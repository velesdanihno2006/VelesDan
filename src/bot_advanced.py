# bot_qwen_together.py  (✓ c кнопками и индикатором ожидания)
import os, logging, tempfile, subprocess
from dotenv import load_dotenv
import telebot, whisper
from telebot import types
from together import Together

# ── 1. env ────────────────────────────────────────────────────────────
load_dotenv()
TG_TOKEN         = os.getenv("TG_TOKEN", "").strip()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "").strip()
if not TG_TOKEN or not TOGETHER_API_KEY:
    raise RuntimeError(".env должен содержать TG_TOKEN и TOGETHER_API_KEY")

# ── 2. init ───────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
bot           = telebot.TeleBot(TG_TOKEN)
whisper_model = whisper.load_model("small")
client        = Together(api_key=TOGETHER_API_KEY)
MODEL_NAME    = "Qwen/Qwen2.5-72B-Instruct-Turbo"

# ── 3. constant ───────────────────────────────────────────────────────
FULL_TEXT_SEC = 5
MAX_DUR_SEC   = 20*60
MAX_CHARS     = 4000
SETTINGS = {
    "short":  ("Сжато изложи основные мысли в 2–3 предложениях.", 120),
    "medium": ("Напиши развёрнутый конспект (5–7 предложений).",   300),
    "long":   ("Составь подробный конспект (10–15 предложений).",  600),
}

# транзитное хранилище {chat_id: текст транскрипта}
pending_text: dict[int, str] = {}

# ── 4. helpers ────────────────────────────────────────────────────────
def to_wav(src: str) -> str:
    dst = src.rsplit(".",1)[0] + ".wav"
    subprocess.run(["ffmpeg","-y","-i",src,"-ar","16000",dst],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return dst

def split_long(txt:str, limit=MAX_CHARS):
    while len(txt) > limit:
        cut = txt.rfind("\n", 0, limit) or limit
        yield txt[:cut].strip(); txt = txt[cut:].lstrip()
    yield txt

def qwen(text:str, mode:str) -> str:
    prompt, max_toks = SETTINGS[mode]
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role":"system","content":"Ты помогаешь студенту делать конспект."},
            {"role":"user",  "content":f"{prompt}\n\nТекст:\n{text}"}
        ],
        temperature=0.0,
        max_tokens=max_toks
    )
    return resp.choices[0].message.content.strip()

def keyboard():
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("⚡ Короткий",  callback_data="short"),
        types.InlineKeyboardButton("📄 Средний", callback_data="medium"),
        types.InlineKeyboardButton("📚 Длинный",   callback_data="long"),
    )
    return kb

# ── 5. /start /help ───────────────────────────────────────────────────
HELP = (
    "Пришли голосовое / MP3 до 20 мин, чтобы получить краткое содержание\n"
)
@bot.message_handler(commands=["start","help"])
def cmd_help(m): bot.send_message(m.chat.id, HELP)

# ── 6. voice / audio ──────────────────────────────────────────────────
@bot.message_handler(content_types=["voice","audio"])
def handle_audio(m):
    fid, dur = (m.voice.file_id, m.voice.duration) if m.content_type=="voice" \
               else (m.audio.file_id, m.audio.duration or 0)
    if dur > MAX_DUR_SEC:
        return bot.reply_to(m, "⚠️ Аудио дольше 20 мин.")
    # download to tmp
    info = bot.get_file(fid); data = bot.download_file(info.file_path)
    src = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg").name
    open(src,"wb").write(data)

    try:
        wav = to_wav(src)
        text = whisper_model.transcribe(wav, fp16=False)["text"].strip()
        logging.info("Транскрипт: %.70s…", text)
        if dur <= FULL_TEXT_SEC:
            for chunk in split_long(text):
                bot.send_message(m.chat.id, f"*Transcript:*\n{chunk}", parse_mode="Markdown")
        else:
            pending_text[m.chat.id] = text    # запоминаем
            bot.send_message(
                m.chat.id,
                "Выберите длину конспекта:",
                reply_markup=keyboard()
            )
    except Exception as e:
        logging.exception("Whisper error")
        bot.reply_to(m, f"⚠️ Ошибка транскрипции: {e}")
    finally:
        for fn in (src, locals().get("wav")):
            if fn and os.path.exists(fn): os.remove(fn)

# ── 7. callback: выбор длины ───────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data in SETTINGS)
def process_choice(call: types.CallbackQuery):
    mode = call.data
    chat_id = call.message.chat.id

    text = pending_text.pop(chat_id, "")
    if not text:
        return bot.answer_callback_query(call.id, "Нет текста для обработки!")

    # сообщение «ожидайте…»
    wait_msg = bot.send_message(chat_id, "⏳ Обрабатываю…")

    try:
        summary = qwen(text, mode)
        for part in split_long(summary):
            bot.send_message(chat_id, f"*Summary ({mode}):*\n{part}", parse_mode="Markdown")
    except Exception as e:
        logging.exception("Qwen error")
        bot.send_message(chat_id, f"⚠️ Ошибка Qwen: {e}")
    finally:
        # удалить «ожидайте…» и кнопки
        bot.delete_message(chat_id, wait_msg.message_id)
        bot.delete_message(chat_id, call.message.message_id)

if __name__ == "__main__":
    logging.info("Polling…")
    bot.infinity_polling(skip_pending=True)
