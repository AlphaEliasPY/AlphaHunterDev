import os
from time import sleep

from HunterAlpha import OWNER_ID, dispatcher
from HunterAlpha.modules.helper_funcs.extraction import extract_user
from HunterAlpha.modules.helper_funcs.chat_status import dev_plus
from HunterAlpha.modules.sql.users_sql import get_user_com_chats
from telegram import Update
from telegram.error import BadRequest, RetryAfter, Unauthorized
from telegram.ext import CallbackContext, CommandHandler, Filters
from telegram.ext.dispatcher import run_async


@dev_plus
def get_user_common_chats(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    user = extract_user(msg, args)
    if not user:
        msg.reply_text("No comparto charlas en común con el vacío.")
        return
    common_list = get_user_com_chats(user)
    if not common_list:
        msg.reply_text("No hay chats comunes con este usuario.!")
        return
    name = bot.get_chat(user).first_name
    text = f"<b>Chats comunes con {name}</b>\n"
    for chat in common_list:
        try:
            chat_name = bot.get_chat(chat).title
            sleep(0.3)
            text += f"• <code>{chat_name}</code>\n"
        except BadRequest:
            pass
        except Unauthorized:
            pass
        except RetryAfter as e:
            sleep(e.retry_after)

    if len(text) < 4096:
        msg.reply_text(text, parse_mode="HTML")
    else:
        with open("common_chats.txt", "w") as f:
            f.write(text)
        with open("common_chats.txt", "rb") as f:
            msg.reply_document(f)
        os.remove("common_chats.txt")


COMMON_CHATS_HANDLER = CommandHandler(
    "getchats", get_user_common_chats, run_async=True
)

dispatcher.add_handler(COMMON_CHATS_HANDLER)
