import os
import time
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# =========================
# Environment & Bot Setup
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment variables")

RSVP_LINK = (
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSdP1mL3VA5soWdIW6t24axo2ikkHAoWhPryXQJoURzoIyqhtw/viewform"
)

bot = telebot.TeleBot(BOT_TOKEN)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================
# Constants
# =========================

SEA = "sea"
NATURE = "nature"
TRAVEL = "travel"

LOOK_PREFIX = "look_"

AUGUST_YES = "august_yes"
AUGUST_NO = "august_no"
RESTART = "restart"
CANT_COME = "cant_come"

# =========================
# State Management
# =========================

user_state: dict[int, set[str]] = {}


def default_options() -> set[str]:
    """Initial set of user preferences."""
    return {SEA, NATURE, TRAVEL}


def reset_user_state(chat_id: int) -> None:
    """Resets user progress to initial state."""
    user_state[chat_id] = default_options()


# =========================
# UI Builders
# =========================

def build_keyboard(options: set[str]) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()

    if SEA in options:
        keyboard.add(
            InlineKeyboardButton("🌊 Море и солнце", callback_data=SEA)
        )
    if TRAVEL in options:
        keyboard.add(
            InlineKeyboardButton(
                "✈️ Путешествие и предвкушение", callback_data=TRAVEL
            )
        )
    if NATURE in options:
        keyboard.add(
            InlineKeyboardButton("🌲 Тишина и природа", callback_data=NATURE)
        )

    return keyboard


# =========================
# Handlers
# =========================

@bot.message_handler(commands=["start"])
def start(message):
    reset_user_state(message.chat.id)

    bot.send_message(
        message.chat.id,
        (
            "Привет 👋\n\n"
            "Мы не знакомы,\n"
            "но я кое-что о тебе знаю 😉\n\n"
            "Лето приближается,\n"
            "а планировать отдых заранее —\n"
            "не совсем твоя история.\n\n"
            "Просто выбери то,\n"
            "что тебе ближе.\n\n"
            "А дальше — сюрприз."
        ),
        reply_markup=build_keyboard(user_state[message.chat.id]),
    )


@bot.message_handler(commands=["restart"])
def restart(message):
    reset_user_state(message.chat.id)
    start(message)


@bot.callback_query_handler(func=lambda call: call.data in {SEA, NATURE, TRAVEL})
def first_choice(call):
    bot.answer_callback_query(call.id)

    chat_id = call.message.chat.id
    user_state.setdefault(chat_id, default_options())

    if call.data == SEA:
        text = (
            "Море — отличный выбор 🌊\n\n"
            "Оно знакомо.\n"
            "Доступно.\n"
            "И почти всегда под рукой.\n\n"
            "Но почему бы не посмотреть\n"
            "на варианты подальше? 😏"
        )
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton("👀 Давай посмотрим", callback_data=f"{LOOK_PREFIX}{SEA}")
        )
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=keyboard)
        return

    if call.data == NATURE:
        text = (
            "Тишина и природа — понятный выбор 🌲\n\n"
            "Иногда хочется просто\n"
            "остановиться и сменить ритм.\n\n"
            "А если найти это\n"
            "в новом месте?"
        )
        keyboard = InlineKeyboardMarkup()
        keyboard.add(
            InlineKeyboardButton(
                "👀 Давай посмотрим", callback_data=f"{LOOK_PREFIX}{NATURE}"
            )
        )
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=keyboard)
        return

    travel_text = (
        "Путешествие и предвкушение ✈️\n\n"
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
        InlineKeyboardButton("☀️ В самый раз", callback_data=AUGUST_YES),
        InlineKeyboardButton("🤔 Ну не знаю", callback_data=AUGUST_NO),
    )

    bot.send_message(
        chat_id,
        (
            "Кстати, раз уж мы заговорили\n"
            "о путешествии…\n\n"
            "У меня есть для тебя предложение.\n"
            "Что насчёт середины августа?"
        ),
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith(LOOK_PREFIX))
def look_further(call):
    bot.answer_callback_query(call.id)

    chat_id = call.message.chat.id
    removed_option = call.data.replace(LOOK_PREFIX, "")
    user_state[chat_id].discard(removed_option)

    bot.edit_message_text(
        "Если оставить привычное «на потом»,\n"
        "что тебе сейчас ближе?",
        chat_id,
        call.message.message_id,
        reply_markup=build_keyboard(user_state[chat_id]),
    )


@bot.callback_query_handler(func=lambda call: call.data in {AUGUST_YES, AUGUST_NO})
def wedding_reveal(call):
    bot.answer_callback_query(call.id)

    chat_id = call.message.chat.id

    poetic_sequence = [
        "Есть даты,\nкоторые не случайны\n\n14 августа —\nодна из них",
        "И есть места,\nособенные места\n\nПрага —\nименно такое",
        "И совсем скоро\nтам начнётся\nчто-то важное",
    ]

    for text in poetic_sequence:
        bot.send_message(chat_id, text)
        time.sleep(2)

    gif_path = os.path.join(BASE_DIR, "Invite.gif")
    with open(gif_path, "rb") as gif:
        bot.send_animation(chat_id, gif, caption="💍")

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("💍 Я приду", url=RSVP_LINK))
    keyboard.add(
        InlineKeyboardButton("😔 К сожалению, не смогу", callback_data=CANT_COME)
    )
    keyboard.add(
        InlineKeyboardButton("🔄 Начать заново", callback_data=RESTART)
    )

    bot.send_message(
        chat_id,
        (
            "Мы будем очень рады,\n"
            "если ты станешь частью\n"
            "этого путешествия 🤍\n\n"
            "Если захочешь вернуться — просто нажми «Начать заново»."
        ),
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda call: call.data == CANT_COME)
def cant_come(call):
    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        (
            "Ничего страшного 🤍\n\n"
            "Планы могут меняться,\n"
            "и мы это прекрасно понимаем.\n\n"
            "До августа ещё есть время —\n"
            "а этот бот всегда будет\n"
            "рад видеть тебя здесь."
        ),
        call.message.chat.id,
        call.message.message_id,
    )


@bot.callback_query_handler(func=lambda call: call.data == RESTART)
def restart_callback(call):
    bot.answer_callback_query(call.id)
    reset_user_state(call.message.chat.id)
    start(call.message)


print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True)
