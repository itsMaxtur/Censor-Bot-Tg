import os
import re
import telebot
from telebot import types
from datetime import datetime, timedelta

api_token = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(api_token)



with open("badwords_regex_combined.txt", "r", encoding="utf-8") as f:
    badwords_pattern = f.read()

badwords_re = re.compile(badwords_pattern, flags=re.IGNORECASE)

def contains_bad_word(text: str) -> bool:

    return badwords_re.search(text) is not None

def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator", "owner")
    except Exception:
        return False


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

@bot.message_handler(func=lambda message: True, content_types=["text"])
def check_message(message):
    if contains_bad_word(message.text):
        try:
            bot.delete_message(message.chat.id, message.message_id)
            restrict_user(message.chat.id, message.from_user.id, 5)

            text = (
                f"⚠️ Пользователь {message.from_user.first_name} нарушил правила.\n"
                f"ID: `{message.from_user.id}`\n\n"
                f"Доступ к сообщениям ограничен на 5 минут."
            )

            bot.send_message(message.chat.id, text, parse_mode="Markdown")

        except Exception as e:
            print("Ошибка при удалении или ограничении:", e)



@bot.message_handler(commands=["unmute"])
def handle_unmute(message):
    chat_id = message.chat.id
    from_id = message.from_user.id

    if not is_admin(chat_id, from_id):
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "❌ Используйте: /unmute <user_id>")
        return

    user_id_str = parts[1].strip()
    if not user_id_str.isdigit():
        bot.reply_to(message, "❌ ID должен быть числом")
        return

    user_id = int(user_id_str)

    try:

        member = bot.get_chat_member(chat_id, user_id)
        if member is None or member.status == "left":
            bot.reply_to(message, f"❌ Пользователь с ID `{user_id}` не найден в этом чате.", parse_mode="Markdown")
            return

        unrestrict_user(chat_id, user_id)
        bot.send_message(chat_id,f"✅ Пользователь {member.user.first_name} разблокирован.\nID: `{user_id}`", parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


@bot.message_handler(commands=["mute"])
def handle_mute(message):
    chat_id = message.chat.id
    from_id = message.from_user.id

    if not is_admin(chat_id, from_id):
        return

    target_id = None
    duration = 5


    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
    else:

        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Используйте: /mute <user_id> [минуты] или ответьте на сообщение нарушителя")
            return
        if not parts[1].isdigit():
            bot.reply_to(message, "❌ ID должен быть числом")
            return
        target_id = int(parts[1])
        target_name = str(target_id)
        if len(parts) > 2 and parts[2].isdigit():
            duration = int(parts[2])

    try:
        member = bot.get_chat_member(chat_id, target_id)
        if member is None or member.status == "left":
            bot.reply_to(message, f"❌ Пользователь с ID `{target_id}` не найден в этом чате.", parse_mode="Markdown")
            return

        restrict_user(chat_id, target_id, duration)
        bot.send_message(chat_id,f"🔇 Пользователь {member.user.first_name} был заблокирован.\nID: `{target_id}`\n⏳ Время: {duration} минут(ы)", parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")


@bot.message_handler(commands=["ban"])
def handle_ban(message):
    chat_id = message.chat.id
    from_id = message.from_user.id

    if not is_admin(chat_id, from_id):
        return

    target_id = None
    delete_all = False

    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
    else:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ Используйте: /ban <user_id> [all] или ответьте на сообщение нарушителя")
            return
        if not parts[1].isdigit():
            bot.reply_to(message, "❌ ID должен быть числом")
            return
        target_id = int(parts[1])
        target_name = str(target_id)
        if len(parts) > 2 and parts[2].lower() == "all":
            delete_all = True

    try:
        member = bot.get_chat_member(chat_id, target_id)
        if member is None or member.status == "left":
            bot.reply_to(message, f"❌ Пользователь с ID `{target_id}` не найден в этом чате.", parse_mode="Markdown")
            return


        bot.ban_chat_member(chat_id, target_id)


        if delete_all:

            messages = bot.get_chat_history(chat_id, limit=100)
            for m in messages:
                if m.from_user and m.from_user.id == target_id:
                    try:
                        bot.delete_message(chat_id, m.message_id)
                    except:
                        pass

        bot.send_message(chat_id,f"⛔ Пользователь {member.user.first_name} был забанен.\nID: `{target_id}`\n{'🧹 Все сообщения удалены.' if delete_all else ''}",parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")



bot.infinity_polling()
