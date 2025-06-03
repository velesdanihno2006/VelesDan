import telebot
from telebot import types
import json
import os
from datetime import datetime

TOKEN = '7487126617:AAE1xCDwWZxmPGZXvXs6_Tr5YXhc2SIXXiI'
bot = telebot.TeleBot(TOKEN)

DATA_FILE = 'users_data.json'

# --- Загрузка данных пользователей ---
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        users_data = json.load(f)
else:
    users_data = {}

def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=4)

def get_user_data(user_id):
    uid = str(user_id)
    if uid not in users_data:
        users_data[uid] = {}
    defaults = {
        'biome': None,
        'climate': None,
        'flora': None,
        'mutations_positive': [],
        'mutations_negative': [],
        'achievements': [],
        'history': []
    }
    for key, default_value in defaults.items():
        if key not in users_data[uid]:
            users_data[uid][key] = default_value
    return users_data[uid]  

def clear_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("Удалить последние данные", callback_data="clear_last"),
        types.InlineKeyboardButton("Удалить все данные", callback_data="clear_all_confirm"),
        types.InlineKeyboardButton("Отмена", callback_data="clear_cancel")
    )
    return markup
# --- Данные для выбора ---

BIOMES = {
    "джунгли": (
        "Плотные тропические леса с высокой влажностью и множеством хищников.\n"
        "Рекомендуется выбирать мутации, повышающие скрытность и устойчивость к ядам.\n"
        "Обрати внимание на улучшенное зрение и ядовитые шипы — они помогут выжить в условиях конкуренции."
    ),
    "пустыня": (
        "Сухая и жаркая местность с ограниченным доступом к воде.\n"
        "Предпочтительны мутации, позволяющие экономить влагу и переносить высокие температуры.\n"
        "Рассмотри терморегуляцию и быстрый метаболизм, чтобы лучше адаптироваться к экстремальным условиям."
    ),
    "ледяные равнины": (
        "Холодные территории с низкими температурами и снежными бурями.\n"
        "Выбирай мутации, улучшающие теплоизоляцию и запас энергии.\n"
        "Крепкие кости и толстая кожа помогут защититься от холода и повреждений."
    ),
    "подводные зоны": (
        "Морские биомы с уникальной флорой и фауной.\n"
        "Полезны мутации, улучшающие дыхание и маневренность под водой.\n"
        "Мощные легкие и острые когти помогут добывать пищу и защищаться."
    ),
    "аномальные области": (
        "Зоны с необычными физическими законами и опасностями.\n"
        "Необходимо выбирать гибкие мутации и адаптации, быстро реагировать на изменения среды.\n"
        "Терморегуляция и улучшенное зрение будут крайне полезны."
    )
}

CLIMATES = {
    "жаркий": (
        "Высокая температура, риск обезвоживания.\n"
        "Обрати внимание на мутации, позволяющие эффективно регулировать температуру тела.\n"
        "Терморегуляция и быстрый метаболизм помогут справиться с жарой."
    ),
    "холодный": (
        "Низкая температура, требуется теплоизоляция.\n"
        "Лучше выбирать мутации с повышенной теплоизоляцией и запасом энергии.\n"
        "Толстая кожа и крепкие кости обеспечат защиту от холода."
    ),
    "влажный": (
        "Высокая влажность, условия для болезней.\n"
        "Предпочтительны мутации с повышенным иммунитетом и способностью противостоять инфекциям.\n"
        "Улучшенное зрение поможет видеть сквозь туман и дождь."
    ),
    "сухой": (
        "Недостаток воды, нужно экономить влагу.\n"
        "Выбирай мутации, минимизирующие потерю воды и повышающие выносливость.\n"
        "Быстрый метаболизм и терморегуляция — ключ к выживанию."
    )
}

FLORA = {
    "ядовитые растения": (
        "Могут нанести урон, но использоваться для мутаций.\n"
        "Обрати внимание на симбиоз с грибами и ядовитые шипы для защиты и атаки.\n"
        "Будь осторожен, но не упускай выгоду."
    ),
    "лечебные травы": (
        "Помогают восстановиться и усилить иммунитет.\n"
        "Рекомендуется сочетать с мутациями, повышающими выносливость и регенерацию.\n"
        "Хороший выбор для долгосрочного выживания."
    ),
    "тяжёлые деревья": (
        "Используются для строительства и защиты.\n"
        "Подойдут мутации, позволяющие строить убежища и ловушки.\n"
        "Симбиоз с флорой усилит защитные возможности."
    ),
    "микроскопические грибы": (
        "Обеспечивают симбиоз и обмен ресурсами.\n"
        "Мутации, повышающие взаимодействие с грибами, откроют новые возможности.\n"
        "Отлично подходят для экосистем с аномалиями."
    )
}

POSITIVE_MUTATIONS = {
    "Крепкие кости": (
        "Увеличивают защиту от физических повреждений.\n"
        "Подходят для биомов с множеством хищников.\n"
        "Рекомендуется в сочетании с толстая кожа."
    ),
    "Острые когти": (
        "Повышают эффективность атаки.\n"
        "Хороший выбор для активных охотников и защитников.\n"
        "Совместимы с ядовитыми шипами для дополнительной защиты."
    ),
    "Быстрый метаболизм": (
        "Ускоряет восстановление сил.\n"
        "Полезен в экстремальных климатических условиях.\n"
        "Помогает адаптироваться к смене биомов."
    ),
    "Терморегуляция": (
        "Позволяет лучше адаптироваться к температурным условиям.\n"
        "Обязательна в жарких и холодных биомах.\n"
        "Снижает стресс и риск обезвоживания."
    ),
    "Улучшенное зрение": (
        "Расширяет поле обзора и реакцию.\n"
        "Необходима для выживания в сложных условиях с множеством опасностей.\n"
        "Помогает обнаружить угрозы на ранней стадии."
    )
}

NEGATIVE_MUTATIONS = {
    "Снижение скорости": (
        "Уменьшает скорость передвижения.\n"
        "Может быть компенсировано увеличенной защитой или силой.\n"
        "Подходит для менее мобильных, но устойчивых к повреждениям существ."
    ),
    "Плохое зрение": (
        "Снижает способность видеть в темноте.\n"
        "Увеличивает риск неожиданной атаки.\n"
        "Лучше избегать, если планируешь активное исследование."
    ),
    "Повышенная уязвимость": (
        "Увеличивает получаемый урон.\n"
        "Следует компенсировать другими мутациями, повышающими защиту.\n"
        "Подходит для создания балансированного риска."
    )
}

ACHIEVEMENTS = [
    "Первый шаг в эволюции",
    "Выжил первую ночь",
    "Освоил новый биом",
    "Создал первое потомство",
    "Изучил базовую технологию",
    "Победил первого хищника",
    "Построил убежище",
    "Заключил симбиоз",
    "Пережил аномалию",
    "Исследовал подводную зону"
]

# --- Меню ---

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Выбрать биом", callback_data="choose_biome"),
        types.InlineKeyboardButton("Выбрать климат", callback_data="choose_climate"),
        types.InlineKeyboardButton("Выбрать флору", callback_data="choose_flora"),
        types.InlineKeyboardButton("Просмотреть мутации", callback_data="view_mutations"),
        types.InlineKeyboardButton("Просмотреть достижения", callback_data="view_achievements"),
        types.InlineKeyboardButton("Добавить достижение", callback_data="add_achievement"),
        types.InlineKeyboardButton("Просмотреть историю", callback_data="view_history"),
        types.InlineKeyboardButton("Очистить данные", callback_data="clear_data"),
        types.InlineKeyboardButton("Помощь", callback_data="help")
    )
    return markup

# --- История пользователя ---

def add_history(user_id, action):
    user_data = get_user_data(user_id)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {action}"
    user_data['history'].append(entry)
    save_data()

def format_history(history_list):
    if not history_list:
        return "История пуста."
    return "\n".join(history_list[-20:])  # последние 20 записей

# --- Команды и обработчик callback ---

@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_data = get_user_data(message.from_user.id)
    text = (
        "Привет, лучшая в мире девочка, прекрасная дева! Это бот-помощник для игры «Эволюция: Миры бесконечной адаптации».\n\n"
        "Выбирай пункты меню, чтобы настроить мир и получить советы по мутациям, "
        "следить за достижениями и планировать развитие существа.\n"
        "Для начала выбери биом."
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())
    add_history(message.from_user.id, "Запустил бота")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    user_data = get_user_data(user_id)

    if call.data == "choose_biome":
        kb = types.InlineKeyboardMarkup(row_width=2)
        for biome in BIOMES.keys():
            kb.add(types.InlineKeyboardButton(biome.capitalize(), callback_data=f"set_biome:{biome}"))
        bot.edit_message_text("Выбери биом:", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data.startswith("set_biome:"):
        biome = call.data.split(":", 1)[1]
        user_data['biome'] = biome
        save_data()
        add_history(user_id, f"Выбрал биом: {biome}")
        bot.edit_message_text(f"Выбран биом: <b>{biome.capitalize()}</b>\n\n{BIOMES[biome]}",
                              call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=main_menu())

    elif call.data == "choose_climate":
        kb = types.InlineKeyboardMarkup(row_width=2)
        for climate in CLIMATES.keys():
            kb.add(types.InlineKeyboardButton(climate.capitalize(), callback_data=f"set_climate:{climate}"))
        bot.edit_message_text("Выбери климат:", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data.startswith("set_climate:"):
        climate = call.data.split(":", 1)[1]
        user_data['climate'] = climate
        save_data()
        add_history(user_id, f"Выбрал климат: {climate}")
        bot.edit_message_text(f"Выбран климат: <b>{climate.capitalize()}</b>\n\n{CLIMATES[climate]}",
                              call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=main_menu())

    elif call.data == "choose_flora":
        kb = types.InlineKeyboardMarkup(row_width=2)
        for flora in FLORA.keys():
            kb.add(types.InlineKeyboardButton(flora.capitalize(), callback_data=f"set_flora:{flora}"))
        bot.edit_message_text("Выбери флору:", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data.startswith("set_flora:"):
        flora = call.data.split(":", 1)[1]
        user_data['flora'] = flora
        save_data()
        add_history(user_id, f"Выбрал флору: {flora}")
        bot.edit_message_text(f"Выбрана флора: <b>{flora.capitalize()}</b>\n\n{FLORA[flora]}",
                              call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=main_menu())

    elif call.data == "view_mutations":
        if not (user_data['biome'] and user_data['climate'] and user_data['flora']):
            bot.answer_callback_query(call.id, "Сначала выбери биом, климат и флору!")
            return

        positive = list(user_data.get('mutations_positive')) or list(POSITIVE_MUTATIONS.keys())[:5]
        negative = list(user_data.get('mutations_negative')) or list(NEGATIVE_MUTATIONS.keys())[:3]

        text = "<b>Рекомендации по положительным мутациям:</b>\n"
        for m in positive:
            desc = POSITIVE_MUTATIONS.get(m, "Описание отсутствует")
            text += f"🟢 {m}: {desc}\n"

        text += "\n<b>Возможные негативные мутации (баланс):</b>\n"
        for m in negative:
            desc = NEGATIVE_MUTATIONS.get(m, "Описание отсутствует")
            text += f"🔴 {m}: {desc}\n"

        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=main_menu())
        add_history(user_id, "Просмотрел рекомендации по мутациям")

    elif call.data == "view_achievements":
        achs = user_data.get('achievements', [])
        if not achs:
            text = "У тебя пока нет достижений."
        else:
            text = "Твои достижения:\n" + "\n".join(f"• {a}" for a in achs)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        add_history(user_id, "Просмотрел достижения")

    elif call.data == "add_achievement":
        kb = types.InlineKeyboardMarkup(row_width=1)
        for i, ach in enumerate(ACHIEVEMENTS):
            kb.add(types.InlineKeyboardButton(ach, callback_data=f"add_ach:{i}"))
        bot.edit_message_text("Выбери достижение для добавления:", call.message.chat.id, call.message.message_id, reply_markup=kb)

    elif call.data.startswith("add_ach:"):
        idx = int(call.data.split(":")[1])
        ach_name = ACHIEVEMENTS[idx]
        if ach_name not in user_data['achievements']:
            user_data['achievements'].append(ach_name)
            save_data()
            add_history(user_id, f"Добавил достижение: {ach_name}")
            msg = f"Достижение <b>{ach_name}</b> добавлено!"
        else:
            msg = "Это достижение уже есть."
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=main_menu())

    elif call.data == "view_history":
        history = user_data.get('history', [])
        bot.edit_message_text(format_history(history), call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        add_history(user_id, "Просмотрел историю")

    elif call.data == "clear_data":
        bot.edit_message_text("Выберите действие очистки данных:", call.message.chat.id, call.message.message_id, reply_markup=clear_menu())

    elif call.data == "clear_last":
    # Например, удаляем последние 5 записей из истории
        history = user_data.get('history', [])
        if len(history) > 5:
            user_data['history'] = history[:-5]
        else:
            user_data['history'] = []
        save_data()
        bot.edit_message_text("Последние данные удалены (последние 5 записей истории).", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        add_history(user_id, "Удалил последние данные")

    elif call.data == "clear_all_confirm":
        users_data[str(user_id)] = {
            'biome': None,
            'climate': None,
            'flora': None,
            'mutations_positive': [],
            'mutations_negative': [],
            'achievements': [],
            'history': []
        }
        save_data()
        bot.edit_message_text("Все данные успешно удалены.", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        add_history(user_id, "Удалил все данные")

    elif call.data == "clear_cancel":
        bot.edit_message_text("Удаление отменено.", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        add_history(user_id, "Отменил удаление данных")


    elif call.data == "help":
        bot.edit_message_text(
            "Это бот-помощник для игры 'Эволюция'. Помогает выбирать мутации, отслеживать достижения и адаптироваться к миру.\n\n"
            "Используй меню для навигации и выбора опций.",
            call.message.chat.id, call.message.message_id, reply_markup=main_menu())
        add_history(user_id, "Просмотрел помощь")

    else:
        bot.answer_callback_query(call.id, "Неизвестная команда.")


bot.polling(none_stop=True)
