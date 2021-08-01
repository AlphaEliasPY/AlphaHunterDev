import html
from typing import Optional

from HunterAlpha import LOGGER, dispatcher
from HunterAlpha.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    connection_status,
    is_user_admin,
    user_admin,
)
from HunterAlpha.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from HunterAlpha.modules.helper_funcs.string_handling import extract_time
from HunterAlpha.modules.log_channel import loggable
from telegram import Bot, Chat, ChatPermissions, ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, run_async
from telegram.utils.helpers import mention_html


def check_user(user_id: int, bot: Bot, chat: Chat) -> Optional[str]:
    if not user_id:
        reply = "Parece que no se está refiriendo a un usuario o el ID especificado es incorrecto.."
        return reply

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            reply = "Parece que no puedo encontrar a este usuario"
            return reply
        else:
            raise

    if user_id == bot.id:
        reply = "No me voy a enmudecer, que tan alto estas?"
        return reply

    if is_user_admin(chat, user_id, member):
        reply = "Hipocresía. Encuentra a alguien más para silenciar, pero no a este."
        return reply

    return None


@connection_status
@bot_admin
@user_admin
@loggable
def mute(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)
    reply = check_user(user_id, bot, chat)

    if reply:
        message.reply_text(reply)
        return ""

    member = chat.get_member(user_id)

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#MUTE\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    if reason:
        log += f"\n<b>Razon:</b> {reason}"

    if member.can_send_messages is None or member.can_send_messages:
        chat_permissions = ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(chat.id, user_id, chat_permissions)
        reply = (
            f"<code>❕</code><b>Mute Event</b>\n"
            f"<code> </code><b>•  User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
            f"<code> </code><b>•  Time: no expiration date</b>"
        )
        if reason:
            reply += f"\n<code> </code><b>•  Reason:</b> {html.escape(reason)}"
        bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML)
        return log

    else:
        message.reply_text("Este usuario ya está silenciado!")

    return ""


@connection_status
@bot_admin
@user_admin
@loggable
def unmute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "Deberá darme un nombre de usuario para activar el sonido o responder a alguien para que se active el sonido."
        )
        return ""

    member = chat.get_member(int(user_id))

    if member.status != "kicked" and member.status != "left":
        if (
            member.can_send_messages
            and member.can_send_media_messages
            and member.can_send_other_messages
            and member.can_add_web_page_previews
        ):
            message.reply_text("Este usuario ya tiene derecho a hablar..")
        else:
            chat_permissions = ChatPermissions(
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
            try:
                bot.restrict_chat_member(chat.id, int(user_id), chat_permissions)
            except BadRequest:
                pass
            bot.sendMessage(
                chat.id,
                f"Yo permitiré <b>{html.escape(member.user.first_name)}</b> textear!",
                parse_mode=ParseMode.HTML,
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNMUTE\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
            )
    else:
        message.reply_text(
            "Este usuario ni siquiera está en el chat, dejar de silenciarlo no lo hará hablar más de lo que dice. "
            "ya lo hacen!"
        )

    return ""


@connection_status
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_mute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = extract_user_and_text(message, args)
    reply = check_user(user_id, bot, chat)

    if reply:
        message.reply_text(reply)
        return ""

    member = chat.get_member(user_id)

    if not reason:
        message.reply_text("No has especificado un momento para silenciar a este usuario.!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#TEMP MUTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        f"<b>Time:</b> {time_val}"
    )
    if reason:
        log += f"\n<b>Razon:</b> {reason}"

    try:
        if member.can_send_messages is None or member.can_send_messages:
            chat_permissions = ChatPermissions(can_send_messages=False)
            bot.restrict_chat_member(
                chat.id, user_id, chat_permissions, until_date=mutetime
            )
            reply = (
                f"<code>❕</code><b>Mute Event</b>\n"
                f"<code> </code><b>•  User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
                f"<code> </code><b>•  Time: {time_val}</b>"
            )
            if reason:
                reply += f"\n<code> </code><b>•  Reason:</b> {html.escape(reason)}"
            bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML)
            return log
        else:
            message.reply_text("Este usuario ya está silenciado.")

    except BadRequest as excp:
        if excp.message == "Mensaje de respuesta no encontrado":
            # Do not reply
            message.reply_text(f"Muted for {time_val}!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR silenciar al usuario %s en el chat %s (%s) debido a %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Bueno maldita sea, no puedo silenciar a ese usuario.")

    return ""


__help__ = """
*Solo administradores:*
 • `/mute <userhandle> <razón> (opcional)`*:* silencia a un usuario. También se puede utilizar como respuesta, silenciando la respuesta al usuario..
 • `/tmute <userhandle> x (m / h / d) <reason> (opcional)`*:* silencia a un usuario por x tiempo. (a través del identificador o respuesta). `m` =` minutos`, `h` =` horas`, `d` =` días`.
 • `/unmute <userhandle>`*:* activa el sonido de un usuario. También se puede utilizar como respuesta, silenciando la respuesta al usuario..
"""

MUTE_HANDLER = CommandHandler("mute", mute, run_async=True)
UNMUTE_HANDLER = CommandHandler("unmute", unmute, run_async=True)
TEMPMUTE_HANDLER = CommandHandler(["tmute", "tempmute"], temp_mute, run_async=True)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)

__mod_name__ = "Silenciar"
__handlers__ = [MUTE_HANDLER, UNMUTE_HANDLER, TEMPMUTE_HANDLER]
