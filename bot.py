import telebot
import time
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN")
RSVP_LINK = "https://docs.google.com/forms/d/e/1FAIpQLSdP1mL3VA5soWdIW6t24axo2ikkHAoWhPryXQJoURzoIyqhtw/viewform"

bot = telebot.TeleBot(BOT_TOKEN)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
user_state = {}


def default_options():
    return {"sea", "nature", "travel"}


def build_keyboard(options):
    keyboard = InlineKeyboardMarkup()
    if "sea" in options:
        keyboard.add(InlineKeyboardButton("🌊 Море и солнце", callback_data="sea"))
    if "travel" in options:
        keyboard.add(InlineKeyboardButton("✈️ Путешествие и город", callback_data="travel"))
    if "nature" in options:
        keyboard.add(InlineKeyboardButton("🌲 Тишина и природа", callback_data="nature"))
    return keyboard


@bot.message_handler(commands=["start"])
def start(message):
    user_state[message.chat.id] = default_options()

    bot.send_message(
        message.chat.id,
        "Привет 👋\n\n"
        "Мы не знакомы,\n"
        "но я кое-что о тебе знаю 😉\n\n"
        "Лето приближается,\n"
        "а планировать отдых заранее —\n"
        "не совсем твоя история.\n\n"
        "Просто выбери то,\n"
        "что тебе ближе.\n\n"
        "А дальше — сюрприз.",
        reply_markup=build_keyboard(user_state[message.chat.id])
    )


@bot.callback_query_handler(func=lambda call: call.data in ["sea", "nature", "travel"])
def first_choice(call):
    chat_id = call.message.chat.id
    user_state.setdefault(chat_id, default_options())

    if call.data == "sea":
        text = (
            "Море — отличный выбор 🌊\n\n"
            "Оно знакомо.\n"
            "Доступно.\n"
            "И почти всегда под рукой.\n\n"
            "Но почему бы не посмотреть\n"
            "на варианты подальше? 😏"
        )
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("👀 Давай посмотрим", callback_data="look_sea"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=keyboard)
        return

    if call.data == "nature":
        text = (
            "Тишина и природа — понятный выбор 🌲\n\n"
            "Иногда хочется просто\n"
            "остановиться и сменить ритм.\n\n"
            "А если найти это\n"
            "в новом месте?"
        )
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("👀 Давай посмотрим", callback_data="look_nature"))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=keyboard)
        return

    travel_text = (
        "Путешествие и город ✈️\n\n"
        "Путешествие — это не про место.\n"
        "Это про смену ритма.\n"
        "Про выход за привычное.\n\n"
        "Но по-настоящему запоминающимся\n"
        "оно становится тогда,\n"
        "когда рядом близкие люди\n"
        "и вас объединяет\n"
        "важное событие."
    )

    bot.edit_message_text(travel_text, chat_id, call.message.message_id)
    time.sleep(2)

    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("☀️ В самый раз", callback_data="august_yes"),
        InlineKeyboardButton("🤔 Ну не знаю", callback_data="august_no")
    )

    bot.send_message(
        chat_id,
        "Кстати, раз уж мы заговорили\n"
        "о путешествии…\n\n"
        "У меня есть для тебя предложение.\n"
        "Что насчёт середины августа?",
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("look_"))
def look_further(call):
    chat_id = call.message.chat.id
    removed = call.data.replace("look_", "")
    user_state[chat_id].discard(removed)

    bot.edit_message_text(
        "Если оставить привычное «на потом»,\n"
        "что тебе сейчас ближе?",
        chat_id,
        call.message.message_id,
        reply_markup=build_keyboard(user_state[chat_id])
    )


@bot.callback_query_handler(func=lambda call: call.data in ["august_yes", "august_no"])
def wedding_reveal(call):
    chat_id = call.message.chat.id

    poetic_sequence = [
        "Есть даты,\nкоторые не случайны\n\n14 августа —\nодна из них",
        "И есть места,\nособенные места\n\nПрага —\nименно такое",
        "И совсем скоро\nтам начнётся\nчто-то важное"
    ]

    for text in poetic_sequence:
        bot.send_message(chat_id, text)
        time.sleep(2)

    gif_path = os.path.join(BASE_DIR, "Invite.gif")
    with open(gif_path, "rb") as gif:
        bot.send_animation(chat_id, gif, caption="💍")

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💍 Я приду", url=RSVP_LINK))
    keyboard.add(InlineKeyboardButton("😔 К сожалению, не смогу", callback_data="cant_come"))

    bot.send_message(
        chat_id,
        "Мы будем очень рады,\n"
        "если ты станешь частью\n"
        "этого путешествия 🤍",
        reply_markup=keyboard
    )


@bot.callback_query_handler(func=lambda call: call.data == "cant_come")
def cant_come(call):
    bot.edit_message_text(
        "Ничего страшного 🤍\n\n"
        "Планы могут меняться,\n"
        "и мы это прекрасно понимаем.\n\n"
        "До августа ещё есть время —\n"
        "а этот бот всегда будет\n"
        "рады видеть тебя здесь.",
        call.message.chat.id,
        call.message.message_id
    )


print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True)
