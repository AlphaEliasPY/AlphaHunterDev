from typing import Optional

import HunterAlpha.modules.sql.rules_sql as sql
from HunterAlpha import dispatcher
from HunterAlpha.modules.helper_funcs.chat_status import user_admin
from HunterAlpha.modules.helper_funcs.string_handling import markdown_parser
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ParseMode,
    Update,
    User,
)
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import escape_markdown


def get_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    send_rules(update, chat_id)


# Do not async - not from a handler
def send_rules(update, chat_id, from_pm=False):
    bot = dispatcher.bot
    user = update.effective_user  # type: Optional[User]
    reply_msg = update.message.reply_to_message
    try:
        chat = bot.get_chat(chat_id)
    except BadRequest as excp:
        if excp.message == "Chat no encontrado" and from_pm:
            bot.send_message(
                user.id,
                "¡El atajo de reglas para este chat no se ha configurado correctamente! Pedir a los administradores que "
                "arregla esto.\nQuizá hayan olvidado el guión en el ID",
            )
            return
        else:
            raise

    rules = sql.get_rules(chat_id)
    text = f"Las reglas para *{escape_markdown(chat.title)}* are:\n\n{rules}"

    if from_pm and rules:
        bot.send_message(
            user.id, text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )
    elif from_pm:
        bot.send_message(
            user.id,
            "Los administradores del grupo aún no han establecido ninguna regla para este chat.. "
            "Sin embargo, esto probablemente no significa que sea ilegal...!",
        )
    elif rules and reply_msg:
        reply_msg.reply_text(
            "Haga clic en el botón de abajo para ver las reglas.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Reglas", url=f"t.me/{bot.username}?start={chat_id}"
                        )
                    ]
                ]
            ),
        )
    elif rules:
        update.effective_message.reply_text(
            "Haga clic en el botón de abajo para ver las reglas.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Reglas", url=f"t.me/{bot.username}?start={chat_id}"
                        )
                    ]
                ]
            ),
        )
    else:
        update.effective_message.reply_text(
            "Los administradores del grupo aún no han establecido ninguna regla para este chat.. "
            "Sin embargo, esto probablemente no significa que sea ilegal...!"
        )


@user_admin
def set_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]
    raw_text = msg.text
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
    if len(args) == 2:
        txt = args[1]
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        markdown_rules = markdown_parser(
            txt, entities=msg.parse_entities(), offset=offset
        )

        sql.set_rules(chat_id, markdown_rules)
        update.effective_message.reply_text("Se establecieron reglas para este grupo con éxito.")


@user_admin
def clear_rules(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    sql.set_rules(chat_id, "")
    update.effective_message.reply_text("Reglas borradas con éxito!")


def __stats__():
    return f"• {sql.num_chats()} los chats tienen reglas establecidas."


def __import_data__(chat_id, data):
    # set chat rules
    rules = data.get("info", {}).get("rules", "")
    sql.set_rules(chat_id, rules)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"Este chat tiene sus reglas establecidas: `{bool(sql.get_rules(chat_id))}`"


__help__ = """
 • `/rules`*:* obtén las reglas para este chat.

*Solo administradores:*
 • `/setrules <sus reglas aquí>`*:* establece las reglas para este chat.
 • `/clearrules`*:* aclara las reglas para este chat.
"""

__mod_name__ = "Reglas"

GET_RULES_HANDLER = CommandHandler("rules", get_rules, filters=Filters.chat_type.groups, run_async=True)
SET_RULES_HANDLER = CommandHandler("setrules", set_rules, filters=Filters.chat_type.groups, run_async=True)
RESET_RULES_HANDLER = CommandHandler("clearrules", clear_rules, filters=Filters.chat_type.groups, run_async=True)

dispatcher.add_handler(GET_RULES_HANDLER)
dispatcher.add_handler(SET_RULES_HANDLER)
dispatcher.add_handler(RESET_RULES_HANDLER)
