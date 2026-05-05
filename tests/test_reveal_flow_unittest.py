import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path


class DummyInlineKeyboardMarkup:
    def __init__(self):
        self.rows = []

    def add(self, *buttons):
        self.rows.append(buttons)


class DummyInlineKeyboardButton:
    def __init__(self, text, callback_data=None, url=None):
        self.text = text
        self.callback_data = callback_data
        self.url = url


class DummyBot:
    def __init__(self, _token):
        pass

    def message_handler(self, *args, **kwargs):
        def decorator(fn):
            return fn

        return decorator

    def callback_query_handler(self, *args, **kwargs):
        def decorator(fn):
            return fn

        return decorator

    def send_message(self, *args, **kwargs):
        return None

    def send_photo(self, *args, **kwargs):
        return None

    def edit_message_text(self, *args, **kwargs):
        return None

    def answer_callback_query(self, *args, **kwargs):
        return None

    def infinity_polling(self, *args, **kwargs):
        return None


class RevealFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        telebot_module = types.ModuleType("telebot")
        telebot_types_module = types.ModuleType("telebot.types")

        telebot_module.TeleBot = DummyBot
        telebot_types_module.InlineKeyboardMarkup = DummyInlineKeyboardMarkup
        telebot_types_module.InlineKeyboardButton = DummyInlineKeyboardButton

        sys.modules["telebot"] = telebot_module
        sys.modules["telebot.types"] = telebot_types_module

        os.environ["BOT_TOKEN"] = "test-token"
        module_path = Path(__file__).resolve().parents[1] / "bot.py"
        spec = importlib.util.spec_from_file_location("bot_under_test_unittest", module_path)
        cls.bot_module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(cls.bot_module)

    def setUp(self):
        self.bot_module.time.sleep = lambda _: None
        self.bot_module.active_reveal_chats.clear()

    def test_reveal_sequence_sends_all_steps(self):
        sent_messages = []
        sent_photos = []

        self.bot_module.bot.send_message = (
            lambda chat_id, text, reply_markup=None: sent_messages.append((chat_id, text, reply_markup))
        )
        self.bot_module.bot.send_photo = (
            lambda chat_id, image_file, caption=None: sent_photos.append((chat_id, caption))
        )

        chat_id = 101
        self.bot_module.active_reveal_chats.add(chat_id)
        self.bot_module.send_wedding_reveal_sequence(chat_id)

        self.assertEqual(len(sent_messages), 4)
        self.assertEqual(len(sent_photos), 1)
        self.assertEqual(sent_photos[0], (chat_id, "💍"))
        self.assertNotIn(chat_id, self.bot_module.active_reveal_chats)

    def test_reveal_sequence_handles_photo_failure(self):
        sent_messages = []

        self.bot_module.bot.send_message = (
            lambda chat_id, text, reply_markup=None: sent_messages.append((chat_id, text, reply_markup))
        )

        def fail_send_photo(*_args, **_kwargs):
            raise RuntimeError("photo failed")

        self.bot_module.bot.send_photo = fail_send_photo

        chat_id = 202
        self.bot_module.active_reveal_chats.add(chat_id)
        self.bot_module.send_wedding_reveal_sequence(chat_id)

        self.assertEqual(len(sent_messages), 3)
        self.assertNotIn(chat_id, self.bot_module.active_reveal_chats)

    def test_wedding_reveal_prevents_duplicate_parallel_run(self):
        started = []

        class DummyThread:
            def __init__(self, target, args, daemon):
                self.target = target
                self.args = args
                self.daemon = daemon

            def start(self):
                started.append(self.args[0])

        self.bot_module.threading.Thread = DummyThread
        self.bot_module.bot.answer_callback_query = lambda _cid: None

        chat_id = 303
        call = types.SimpleNamespace(
            id="cbq",
            message=types.SimpleNamespace(chat=types.SimpleNamespace(id=chat_id)),
        )

        self.bot_module.wedding_reveal(call)
        self.bot_module.wedding_reveal(call)

        self.assertEqual(started, [chat_id])


if __name__ == "__main__":
    unittest.main(verbosity=2)
