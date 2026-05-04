import os
import threading
import time
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# =========================
# Environment & Bot Setup
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in environment variables")

RSVP_YES_LINK = os.getenv(
    "RSVP_YES_LINK",
    "https://docs.google.com/forms/d/e/"
    "1FAIpQLSdP1mL3VA5soWdIW6t24axo2ikkHAoWhPryXQJoURzoIyqhtw/viewform"
)
RSVP_MAYBE_LINK = os.getenv("RSVP_MAYBE_LINK", RSVP_YES_LINK)

bot = telebot.TeleBot(BOT_TOKEN)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INVITE_IMAGE_PATH = os.path.join(BASE_DIR, "Invite.png")

# =========================
# Constants
# =========================

SEA = "sea"
NATURE = "nature"
TRAVEL = "travel"

LOOK_PREFIX = "look_"

AUGUST_YES = "august_yes"
AUGUST_NO = "august_no"
CANT_COME = "cant_come"
RSVP_MAYBE_CALLBACK = "rsvp_maybe_callback"

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


def send_invite_image(chat_id: int) -> None:
    """Sends the invitation as a photo attachment."""
    with open(INVITE_IMAGE_PATH, "rb") as image_file:
        bot.send_photo(chat_id, image_file, caption="💍")


def build_final_rsvp_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🥳 С удовольствием", url=RSVP_YES_LINK),
        InlineKeyboardButton("🤔 Нужно подумать", callback_data=RSVP_MAYBE_CALLBACK),
    )
    keyboard.add(
        InlineKeyboardButton("😔 К сожалению, не смогу", callback_data=CANT_COME)
    )
    return keyboard


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
            "А если найти это в новом месте?"
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
        "и вас объединяет важное событие."
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
    user_state.setdefault(chat_id, default_options())
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
    threading.Thread(
        target=send_wedding_reveal_sequence,
        args=(chat_id,),
        daemon=True,
    ).start()


@bot.callback_query_handler(func=lambda call: call.data == RSVP_MAYBE_CALLBACK)
def maybe_rsvp(call):
    bot.answer_callback_query(call.id)

    chat_id = call.message.chat.id
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Открыть форму", url=RSVP_MAYBE_LINK))

    bot.send_message(
        chat_id,
        (
            "Ничего страшного 🤍\n\n"
            "Планы иногда меняются,\n"
            "и это абсолютно нормально.\n\n"
            "До августа ещё есть время —\n"
            "а пока можешь заполнить форму,\n"
            "чтобы мы оставались на связи.\n\n"
            "Будем рады увидеть тебя,\n"
            "если всё сложится ✨"
        ),
        reply_markup=keyboard,
    )


def send_wedding_reveal_sequence(chat_id: int) -> None:
    poetic_sequence = [
        "Есть даты,\nкоторые не случайны\n\n14 августа — одна из них",
        "И есть места,\nособенные места\n\nПрага — именно такое",
        "И совсем скоро\nтам начнётся что-то важное",
    ]

    for text in poetic_sequence:
        bot.send_message(chat_id, text)
        time.sleep(2)

    send_invite_image(chat_id)
    time.sleep(2)

    bot.send_message(
        chat_id,
        (
            "Мы будем очень рады,\n"
            "если ты станешь частью\n"
            "этого путешествия 💍"
        ),
        reply_markup=build_final_rsvp_keyboard(),
    )


@bot.callback_query_handler(func=lambda call: call.data == CANT_COME)
def cant_come(call):
    bot.answer_callback_query(call.id)

    chat_id = call.message.chat.id

    bot.edit_message_text(
        (
            "Ничего страшного 🤍\n\n"
            "Планы могут меняться,\n"
            "и мы это прекрасно понимаем.\n\n"
            "До августа ещё есть время —\n"
            "а этот бот всегда будет\n"
            "рад видеть тебя здесь."
        ),
        chat_id,
        call.message.message_id,
    )


print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True)



