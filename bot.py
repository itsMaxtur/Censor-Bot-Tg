import os
import re
import telebot
from telebot import types
from datetime import datetime, timedelta

api_token = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(api_token)



with open("badwords_regex_combined.txt", "r", encoding="utf-8") as f:
    BADWORDS_PATTERN = f.read()

BADWORDS_RE = re.compile(BADWORDS_PATTERN, flags=re.IGNORECASE)

def contains_bad_word(text: str) -> bool:

    return BADWORDS_RE.search(text) is not None


def restrict_user(chat_id, user_id, duration_minutes=5):
    until_date = datetime.now() + timedelta(minutes=duration_minutes)
    bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions=types.ChatPermissions(can_send_messages=False,
                                          can_send_media_messages=False,
                                          can_send_other_messages=False,
                                          can_add_web_page_previews=False),
        until_date=until_date
    )


def unrestrict_user(chat_id, user_id):
    bot.restrict_chat_member(
        chat_id,
        user_id,
        permissions=types.ChatPermissions(can_send_messages=True,
                                          can_send_media_messages=True,
                                          can_send_other_messages=True,
                                          can_add_web_page_previews=True),
        until_date=0
    )


@bot.message_handler(func=lambda message: True, content_types=["text"])
def check_message(message):
    if contains_bad_word(message.text):
        try:
            bot.delete_message(message.chat.id, message.message_id)
            restrict_user(message.chat.id, message.from_user.id, 5)
            bot.send_message(message.chat.id, f"⚠️ Пользователь {message.from_user.first_name} нарушил правила. "
                                              f"Доступ к сообщениям ограничен на 5 минут.")
        except Exception as e:
            print("Ошибка при удалении или ограничении:", e)

@bot.message_handler(commands=["unmute"])
def handle_unmute(message):
    if not message.reply_to_message and len(message.text.split()) < 2:
        bot.reply_to(message, "❌ Используйте: /unmute @username (или ответьте на сообщение)")
        return

    chat_id = message.chat.id

    try:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            unrestrict_user(chat_id, user_id)
            bot.reply_to(message, f"✅ Пользователь {message.reply_to_message.from_user.first_name} разблокирован.")
        else:
            username = message.text.split()[1]
            member = bot.get_chat_member(chat_id, username)
            user_id = member.user.id
            unrestrict_user(chat_id, user_id)
            bot.reply_to(message, f"✅ Пользователь {username} разблокирован.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")



bot.infinity_polling()
