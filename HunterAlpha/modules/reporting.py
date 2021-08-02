import html

from HunterAlpha import LOGGER, SUDO_USERS, WHITELIST_USERS, dispatcher
from HunterAlpha.modules.helper_funcs.chat_status import user_admin, user_not_admin
from HunterAlpha.modules.log_channel import loggable
from HunterAlpha.modules.sql import reporting_sql as sql
from telegram import Chat, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import BadRequest, Unauthorized
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)
from telegram.utils.helpers import mention_html

REPORT_GROUP = 12
REPORT_IMMUNE_USERS = SUDO_USERS + WHITELIST_USERS


@user_admin
def report_setting(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type == chat.PRIVATE:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_user_setting(chat.id, True)
                msg.reply_text(
                    "Encendido reportajes! Recibirás una notificación cada vez que alguien informe algo."
                )

            elif args[0] in ("no", "off"):
                sql.set_user_setting(chat.id, False)
                msg.reply_text("¡Desactivado los informes! No recibirás ningún informe.")
        else:
            msg.reply_text(
                f"Su preferencia de informe actual es: `{sql.user_should_report(chat.id)}`",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if len(args) >= 1:
            if args[0] in ("yes", "on"):
                sql.set_chat_setting(chat.id, True)
                msg.reply_text(
                    "Encendido reportajes! Los administradores que hayan activado los informes recibirán una notificación cuando /report "
                    "o @admin se llama."
                )

            elif args[0] in ("no", "off"):
                sql.set_chat_setting(chat.id, False)
                msg.reply_text(
                    "Desactivado los informes! No se notificará a ningún administrador el /report o @admin."
                )
        else:
            msg.reply_text(
                f"La configuración actual de este grupo es: `{sql.chat_should_report(chat.id)}`",
                parse_mode=ParseMode.MARKDOWN,
            )


@user_not_admin
@loggable
def report(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user
        chat_name = chat.title or chat.first or chat.username
        admin_list = chat.get_administrators()
        message = update.effective_message

        if not args:
            message.reply_text("Agregue un motivo para informar primero.")
            return ""

        if user.id == reported_user.id:
            message.reply_text("Uh si, seguro seguro ... mucho mas?")
            return ""

        if user.id == bot.id:
            message.reply_text("Buen intento.")
            return ""

        if reported_user.id in REPORT_IMMUNE_USERS:
            message.reply_text("¿Oh? Estás denunciando a un superusuario?")
            return ""

        if chat.username and chat.type == Chat.SUPERGROUP:

            reported = f"{mention_html(user.id, user.first_name)} informó {mention_html(reported_user.id, reported_user.first_name)} A los administradores!"

            msg = (
                f"<b>⚠️Reporte: </b>{html.escape(chat.title)}\n"
                f"<b> • Reporte por:</b> {mention_html(user.id, user.first_name)}(<code>{user.id}</code>)\n"
                f"<b> • Usuario reportado:</b> {mention_html(reported_user.id, reported_user.first_name)} (<code>{reported_user.id}</code>)\n"
            )
            link = f'<b> • Mensaje informado:</b> <a href="https://t.me/{chat.username}/{message.reply_to_message.message_id}">haga clic aquí</a>'
            should_forward = False
            keyboard = [
                [
                    InlineKeyboardButton(
                        "➡ Mensaje",
                        url=f"https://t.me/{chat.username}/{message.reply_to_message.message_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⚠ Patear",
                        callback_data=f"report_{chat.id}=kick={reported_user.id}={reported_user.first_name}",
                    ),
                    InlineKeyboardButton(
                        "⛔️ Prohibir",
                        callback_data=f"report_{chat.id}=banned={reported_user.id}={reported_user.first_name}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "❎ Borrar mensaje",
                        callback_data=f"report_{chat.id}=delete={reported_user.id}={message.reply_to_message.message_id}",
                    )
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        else:
            reported = (
                f"{mention_html(user.id, user.first_name)} reportado "
                f"{mention_html(reported_user.id, reported_user.first_name)} A los administradores!"
            )

            msg = f'{mention_html(user.id, user.first_name)} Está llamando a los administradores en "{html.escape(chat_name)}"!'
            link = ""
            should_forward = True

        for admin in admin_list:
            if admin.user.is_bot:  # can't message bots
                continue

            if sql.user_should_report(admin.user.id):
                try:
                    if not chat.type == Chat.SUPERGROUP:
                        bot.send_message(
                            admin.user.id, msg + link, parse_mode=ParseMode.HTML
                        )

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if (
                                len(message.text.split()) > 1
                            ):  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)
                    if not chat.username:
                        bot.send_message(
                            admin.user.id, msg + link, parse_mode=ParseMode.HTML
                        )

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if (
                                len(message.text.split()) > 1
                            ):  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                    if chat.username and chat.type == Chat.SUPERGROUP:
                        bot.send_message(
                            admin.user.id,
                            msg + link,
                            parse_mode=ParseMode.HTML,
                            reply_markup=reply_markup,
                        )

                        if should_forward:
                            message.reply_to_message.forward(admin.user.id)

                            if (
                                len(message.text.split()) > 1
                            ):  # If user is giving a reason, send his message too
                                message.forward(admin.user.id)

                except Unauthorized:
                    pass
                except BadRequest as excp:  # TODO: cleanup exceptions
                    LOGGER.exception("Exception while reporting user")

        message.reply_to_message.reply_text(
            f"{mention_html(user.id, user.first_name)} informó el mensaje a los administradores.",
            parse_mode=ParseMode.HTML,
        )
        return msg

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, _):
    return f"Este chat está configurado para enviar informes de usuario a los administradores, a través de /report y @admin: `{sql.chat_should_report(chat_id)}`"


def __user_settings__(user_id):
    if sql.user_should_report(user_id) is True:
        text = "Recibirás informes de los chats que eres administrador."
    else:
        text = "*No* recibirás informes de los chats que eres administrador."
    return text


def buttons(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    splitter = query.data.replace("report_", "").split("=")
    if splitter[1] == "kick":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            bot.unbanChatMember(splitter[0], splitter[2])
            query.answer("✅ Pateado con éxito")
            return ""
        except Exception as err:
            query.answer("🛑 No se pudo perforar")
            bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
    elif splitter[1] == "banned":
        try:
            bot.kickChatMember(splitter[0], splitter[2])
            query.answer("✅  Prohibido con éxito")
            return ""
        except Exception as err:
            bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
            query.answer("🛑 No se pudo prohibir")
    elif splitter[1] == "delete":
        try:
            bot.deleteMessage(splitter[0], splitter[3])
            query.answer("✅ Mensaje borrado")
            return ""
        except Exception as err:
            bot.sendMessage(
                text=f"Error: {err}",
                chat_id=query.message.chat_id,
                parse_mode=ParseMode.HTML,
            )
            query.answer("🛑 No se pudo borrar el mensaje!")


__help__ = """
 • `/report <razón>`*:* responder a un mensaje para informar a los administradores.
 • `@admin`*:* responder a un mensaje para informar a los administradores.
*NOTA:* Ninguno de estos se activará si lo utilizan los administradores.

*Solo administradores:*
 • `/reports <on/off>`*:* cambiar la configuración del informe o ver el estado actual.
   • Si lo hace en pm, cambia su estado.
   • Si está en grupo, cambia el estado de ese grupo.
"""

SETTING_HANDLER = CommandHandler("reports", report_setting, run_async=True)
REPORT_HANDLER = CommandHandler("report", report, filters=Filters.chat_type.groups, run_async=True)
ADMIN_REPORT_HANDLER = MessageHandler(Filters.regex(r"(?i)@admin(s)?"), report)

REPORT_BUTTON_USER_HANDLER = CallbackQueryHandler(buttons, pattern=r"report_")
dispatcher.add_handler(REPORT_BUTTON_USER_HANDLER)

dispatcher.add_handler(SETTING_HANDLER)
dispatcher.add_handler(REPORT_HANDLER, REPORT_GROUP)
dispatcher.add_handler(ADMIN_REPORT_HANDLER, REPORT_GROUP)

__mod_name__ = "Reportes"
__handlers__ = [
    (REPORT_HANDLER, REPORT_GROUP),
    (ADMIN_REPORT_HANDLER, REPORT_GROUP),
    (SETTING_HANDLER),
]
