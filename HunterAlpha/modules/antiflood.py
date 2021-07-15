import html
from typing import Optional, List
import re

from telegram import Message, Chat, Update, User, ChatPermissions

from HunterAlpha import WHITELIST_USERS, dispatcher
from HunterAlpha.modules.helper_funcs.chat_status import (
    bot_admin,
    is_user_admin,
    user_admin,
    user_admin_no_reply,
)
from HunterAlpha.modules.log_channel import loggable
from HunterAlpha.modules.sql import antiflood_sql as sql
from telegram.error import BadRequest
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)
from telegram.utils.helpers import mention_html, escape_markdown
from HunterAlpha.modules.helper_funcs.string_handling import extract_time
from HunterAlpha.modules.connection import connected
from HunterAlpha.modules.helper_funcs.alternate import send_message
from HunterAlpha.modules.sql.approve_sql import is_approved

FLOOD_GROUP = 3


@loggable
def check_flood(update: Update, context: CallbackContext) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    if not user:  # ignore channels
        return ""

    # ignore admins and whitelists
    if is_user_admin(chat, user.id) or user.id in WHITELIST_USERS:
        sql.update_flood(chat.id, None)
        return ""
    # ignore approved users
    if is_approved(chat.id, user.id):
        sql.update_flood(chat.id, None)
        return
    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            chat.kick_member(user.id)
            execstrings = "Banned"
            tag = "BANNED"
        elif getmode == 2:
            chat.kick_member(user.id)
            chat.unban_member(user.id)
            execstrings = "Kicked"
            tag = "KICKED"
        elif getmode == 3:
            context.bot.restrict_chat_member(
                chat.id, user.id, permissions=ChatPermissions(can_send_messages=False)
            )
            execstrings = "Muted"
            tag = "MUTED"
        elif getmode == 4:
            bantime = extract_time(msg, getvalue)
            chat.kick_member(user.id, until_date=bantime)
            execstrings = "Prohibido por {}".format(getvalue)
            tag = "TBAN"
        elif getmode == 5:
            mutetime = extract_time(msg, getvalue)
            context.bot.restrict_chat_member(
                chat.id,
                user.id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "Silenciado por {}".format(getvalue)
            tag = "TMUTE"
        send_message(
            update.effective_message, "¡Bip, bip! Boop Beep!\n{}!".format(execstrings)
        )

        return (
            "<b>{}:</b>"
            "\n#{}"
            "\n<b>User:</b> {}"
            "\nFlooded the group.".format(
                tag,
                html.escape(chat.title),
                mention_html(user.id, html.escape(user.first_name)),
            )
        )

    except BadRequest:
        msg.reply_text(
            "No puedo restringir a las personas aquí, ¡dame permisos primero! Hasta entonces, deshabilitaré el anti-inundación.."
        )
        sql.set_flood(chat.id, 0)
        return (
            "<b>{}:</b>"
            "\n#INFO"
            "\nNo tengo suficiente permiso para restringir a los usuarios, por lo que la función anti-inundación se desactiva automáticamente".format(
                chat.title
            )
        )


@user_admin_no_reply
@bot_admin
def flood_button(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    match = re.match(r"unmute_flooder\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat = update.effective_chat.id
        try:
            bot.restrict_chat_member(
                chat,
                int(user_id),
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            update.effective_message.edit_text(
                f"No silenciado por {mention_html(user.id, html.escape(user.first_name))}.",
                parse_mode="HTML",
            )
        except:
            pass


@user_admin
@loggable
def set_flood(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "Este comando está destinado a usarse en grupo, no en PM",
            )
            return ""
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if len(args) >= 1:
        val = args[0].lower()
        if val in ["off", "no", "0"]:
            sql.set_flood(chat_id, 0)
            if conn:
                text = message.reply_text(
                    "Anti-inundación ha sido deshabilitado en {}.".format(chat_name)
                )
            else:
                text = message.reply_text("Anti-inundación ha sido deshabilitado.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat_id, 0)
                if conn:
                    text = message.reply_text(
                        "Anti-inundacion ha sido deshabilitado en {}.".format(chat_name)
                    )
                else:
                    text = message.reply_text("Anti-inundación ha sido deshabilitado.")
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin:</b> {}"
                    "\nDisable antiflood.".format(
                        html.escape(chat_name),
                        mention_html(user.id, html.escape(user.first_name)),
                    )
                )

            elif amount <= 3:
                send_message(
                    update.effective_message,
                    "La anti-inudación debe ser 0 (deshabilitada) o un número mayor que 3!",
                )
                return ""

            else:
                sql.set_flood(chat_id, amount)
                if conn:
                    text = message.reply_text(
                        "Anti-inundacion se ha configurado para {} en el chat: {}".format(
                            amount, chat_name
                        )
                    )
                else:
                    text = message.reply_text(
                        "Límite anti-inundación actualizado con éxito para {}!".format(amount)
                    )
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin:</b> {}"
                    "\nSet antiflood to <code>{}</code>.".format(
                        html.escape(chat_name),
                        mention_html(user.id, html.escape(user.first_name)),
                        amount,
                    )
                )

        else:
            message.reply_text("Argumento no válido por favor use un número, 'off' o 'no'")
    else:
        message.reply_text(
            (
                "Use `/setflood numero` para habilitar anti-inundaciones.\nO use `/setflood off` para deshabilitar el anti-inundación!."
            ),
            parse_mode="markdown",
        )
    return ""


def flood(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message

    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "Este comando está destinado a usarse en grupo, no en PM",
            )
            return
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        if conn:
            text = msg.reply_text(
                "No estoy imponiendo ningún control de inundaciones en {}!".format(chat_name)
            )
        else:
            text = msg.reply_text("No estoy imponiendo ningún control de inundaciones aquí!")
    else:
        if conn:
            text = msg.reply_text(
                "Actualmente estoy restringiendo miembros después de {} mensajes consecutivos en {}.".format(
                    limit, chat_name
                )
            )
        else:
            text = msg.reply_text(
                "Actualmente estoy restringiendo miembros después de {} mensajes consecutivos en.".format(
                    limit
                )
            )


@user_admin
def set_flood_mode(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "Este comando está destinado a usarse en grupo, no en PM",
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() == "ban":
            settypeflood = "ban"
            sql.set_flood_strength(chat_id, 1, "0")
        elif args[0].lower() == "kick":
            settypeflood = "kick"
            sql.set_flood_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeflood = "mute"
            sql.set_flood_strength(chat_id, 3, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = """Parece que intentó establecer el valor de tiempo para el antiflood pero no especificó el tiempo; Pruebe, `/ setfloodmode tban <valor de tiempo>`.
Ejemplos de valor de tiempo: 4m = 4 minutos, 3h = 3 horas, 6d = 6 días, 5w = 5 semanas."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return
            settypeflood = "Prohibido por {}".format(args[1])
            sql.set_flood_strength(chat_id, 4, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = (
                    update.effective_message,
                    """Parece que intentó establecer el valor de tiempo para el antiflood pero no especificó el tiempo; Pruebe, `/ setfloodmode tban <valor de tiempo>`.
Ejemplos de valor de tiempo: 4m = 4 minutos, 3h = 3 horas, 6d = 6 días, 5w = 5 semanas.""",
                )
                send_message(update.effective_message, teks, parse_mode="markdown")
                return
            settypeflood = "Silenciado por {}".format(args[1])
            sql.set_flood_strength(chat_id, 5, str(args[1]))
        else:
            send_message(
                update.effective_message, "Solo entiendo ban/kick/mute/tban/tmute!"
            )
            return
        if conn:
            text = msg.reply_text(
                "Exceder el límite de inundación consecutiva resultará en {} en {}!".format(
                    settypeflood, chat_name
                )
            )
        else:
            text = msg.reply_text(
                "Exceder el límite de inundación consecutiva resultará en {}!".format(
                    settypeflood
                )
            )
        return (
            "<b>{}:</b>\n"
            "<b>Admin:</b> {}\n"
            "Ha cambiado el modo antiinundación. El usuario {}.".format(
                settypeflood,
                html.escape(chat.title),
                mention_html(user.id, html.escape(user.first_name)),
            )
        )
    else:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            settypeflood = "ban"
        elif getmode == 2:
            settypeflood = "kick"
        elif getmode == 3:
            settypeflood = "mute"
        elif getmode == 4:
            settypeflood = "tban for {}".format(getvalue)
        elif getmode == 5:
            settypeflood = "tmute for {}".format(getvalue)
        if conn:
            text = msg.reply_text(
                "Enviar más mensajes que el límite de inundación resultará en {} en {}.".format(
                    settypeflood, chat_name
                )
            )
        else:
            text = msg.reply_text(
                "Sending more message than flood limit will result in {}.".format(
                    settypeflood
                )
            )
    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "No hacer cumplir el control de inundaciones."
    else:
        return "Antiflood has been set to`{}`.".format(limit)


__help__ = """
Anti-inudacion te permite tomar medidas sobre los usuarios que envían más de x mensajes seguidos. Superando la inundación establecida \
resultará en la restricción de ese usuario.
  Esto silenciará a los usuarios si envían más de 10 mensajes seguidos, los bots se ignoran.
 • `/flood`*:* Get the current flood control setting
• *Solo Administradores:*
 • `/setflood <int/'no'/'off'>`*:* habilita o deshabilita el control de inundaciones
 *Example:* `/setflood 10`
 • `/setfloodmode <ban/kick/mute/tban/tmute> <valor>`*:* Acción a realizar cuando el usuario ha superado el límite de inundación. ban/kick/mute/tmute/tban
• *Nota:*
 • Se debe completar el valor para tban y tmute!!
 It can be:
 `5m` = 5 minutos
 `6h` = 6 horas
 `3d` = 3 dias
 `1w` = 1 semanas
 """

__mod_name__ = "Anti-inundacion"

FLOOD_BAN_HANDLER = MessageHandler(
    Filters.all & ~Filters.status_update & Filters.chat_type.groups, check_flood, run_async=True
)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, filters=Filters.chat_type.groups, run_async=True)
SET_FLOOD_MODE_HANDLER = CommandHandler(
    "setfloodmode", set_flood_mode, run_async=True
)  # , filters=Filters.chat_type.groups)
FLOOD_QUERY_HANDLER = CallbackQueryHandler(flood_button, pattern=r"unmute_flooder", run_async=True)
FLOOD_HANDLER = CommandHandler("flood", flood, filters=Filters.chat_type.groups, run_async=True)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(FLOOD_QUERY_HANDLER)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(SET_FLOOD_MODE_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)

__handlers__ = [
    (FLOOD_BAN_HANDLER, FLOOD_GROUP),
    SET_FLOOD_HANDLER,
    FLOOD_HANDLER,
    SET_FLOOD_MODE_HANDLER,
]
