import os
import subprocess
import sys

from contextlib import suppress
from time import sleep

import HunterAlpha

from HunterAlpha import dispatcher
from HunterAlpha.modules.helper_funcs.chat_status import dev_plus
from telegram import TelegramError, Update
from telegram.error import Unauthorized
from telegram.ext import CallbackContext, CommandHandler, run_async


@dev_plus
def allow_groups(update: Update, context: CallbackContext):
    args = context.args
    if not args:
        state = "El bloqueo es " + "on" if not HunterAlpha.ALLOW_CHATS else "off"
        update.effective_message.reply_text(f"Current state: {state}")
        return
    if args[0].lower() in ["off", "no"]:
        HunterAlpha.ALLOW_CHATS = True
    elif args[0].lower() in ["yes", "on"]:
        HunterAlpha.ALLOW_CHATS = False
    else:
        update.effective_message.reply_text("Formato: /lockdown Yes/No o Off/On")
        return
    update.effective_message.reply_text("Hecho! Valor de bloqueo activado.")


@dev_plus
def leave(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if args:
        chat_id = str(args[0])
        try:
            bot.leave_chat(int(chat_id))
        except TelegramError:
            update.effective_message.reply_text(
                "Beep boop, no pude dejar ese grupo (no sé por qué)."
            )
            return
        with suppress(Unauthorized):
            update.effective_message.reply_text("Beep boop, dejé esa sopa!.")
    else:
        update.effective_message.reply_text("Envíe una ID de chat válida")


LEAVE_HANDLER = CommandHandler("leave", leave, run_async=True)
ALLOWGROUPS_HANDLER = CommandHandler("lockdown", allow_groups, run_async=True)

dispatcher.add_handler(ALLOWGROUPS_HANDLER)
dispatcher.add_handler(LEAVE_HANDLER)

__mod_name__ = "Developer"
__handlers__ = [LEAVE_HANDLER, ALLOWGROUPS_HANDLER]
