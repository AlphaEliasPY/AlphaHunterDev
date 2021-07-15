import html
import re

from telegram import ParseMode, ChatPermissions, Update
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, CallbackContext, Filters, run_async
from telegram.utils.helpers import mention_html

import HunterAlpha.modules.sql.blacklist_sql as sql
from HunterAlpha import dispatcher, LOGGER
from HunterAlpha.modules.disable import DisableAbleCommandHandler
from HunterAlpha.modules.helper_funcs.chat_status import user_admin, user_not_admin
from HunterAlpha.modules.helper_funcs.extraction import extract_text
from HunterAlpha.modules.helper_funcs.misc import split_message
from HunterAlpha.modules.log_channel import loggable
from HunterAlpha.modules.warns import warn
from HunterAlpha.modules.helper_funcs.string_handling import extract_time
from HunterAlpha.modules.connection import connected
from HunterAlpha.modules.sql.approve_sql import is_approved
from HunterAlpha.modules.helper_funcs.alternate import send_message, typing_action

BLACKLIST_GROUP = 11


@user_admin
@typing_action
def blacklist(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if chat.type == "private":
            return
        chat_id = update.effective_chat.id
        chat_name = chat.title

    filter_list = "Palabras actuales en la lista negra en <b>{}</b>:\n".format(chat_name)

    all_blacklisted = sql.get_chat_blacklist(chat_id)

    if len(args) > 0 and args[0].lower() == "copy":
        for trigger in all_blacklisted:
            filter_list += "<code>{}</code>\n".format(html.escape(trigger))
    else:
        for trigger in all_blacklisted:
            filter_list += " - <code>{}</code>\n".format(html.escape(trigger))

    # for trigger in all_blacklisted:
    #     filter_list += " - <code>{}</code>\n".format(html.escape(trigger))

    split_text = split_message(filter_list)
    for text in split_text:
        if filter_list == "Palabras actuales en la lista negra en <b>{}</b>:\n".format(
            html.escape(chat_name)
        ):
            send_message(
                update.effective_message,
                "No hay palabras en la lista negra en <b>{}</b>!".format(html.escape(chat_name)),
                parse_mode=ParseMode.HTML,
            )
            return
        send_message(update.effective_message, text, parse_mode=ParseMode.HTML)


@user_admin
@typing_action
def add_blacklist(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    words = msg.text.split(None, 1)

    conn = connected(context.bot, update, chat, user.id)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        else:
            chat_name = chat.title

    if len(words) > 1:
        text = words[1]
        to_blacklist = list(
            {trigger.strip() for trigger in text.split("\n") if trigger.strip()}
        )
        for trigger in to_blacklist:
            sql.add_to_blacklist(chat_id, trigger.lower())

        if len(to_blacklist) == 1:
            send_message(
                update.effective_message,
                "Lista negra agregada <code>{}</code> en el chat: <b>{}</b>!".format(
                    html.escape(to_blacklist[0]), html.escape(chat_name)
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            send_message(
                update.effective_message,
                "Activador de lista negra agregado: <code>{}</code> en <b>{}</b>!".format(
                    len(to_blacklist), html.escape(chat_name)
                ),
                parse_mode=ParseMode.HTML,
            )

    else:
        send_message(
            update.effective_message,
            "Dime qué palabras te gustaría agregar a la lista negra..",
        )


@user_admin
@typing_action
def unblacklist(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    words = msg.text.split(None, 1)

    conn = connected(context.bot, update, chat, user.id)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        else:
            chat_name = chat.title

    if len(words) > 1:
        text = words[1]
        to_unblacklist = list(
            {trigger.strip() for trigger in text.split("\n") if trigger.strip()}
        )
        successful = 0
        for trigger in to_unblacklist:
            success = sql.rm_from_blacklist(chat_id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                send_message(
                    update.effective_message,
                    "Removido <code>{}</code> de la lista negra en <b>{}</b>!".format(
                        html.escape(to_unblacklist[0]), html.escape(chat_name)
                    ),
                    parse_mode=ParseMode.HTML,
                )
            else:
                send_message(
                    update.effective_message, "This is not a blacklist trigger!"
                )

        elif successful == len(to_unblacklist):
            send_message(
                update.effective_message,
                "Removido <code>{}</code> de la lista negra en <b>{}</b>!".format(
                    successful, html.escape(chat_name)
                ),
                parse_mode=ParseMode.HTML,
            )

        elif not successful:
            send_message(
                update.effective_message,
                "Ninguno de estos desencadenantes existe, por lo que no se puede eliminar..",
                parse_mode=ParseMode.HTML,
            )

        else:
            send_message(
                update.effective_message,
                "Removido <code>{}</code> de la lista negra. {} no existió, "
                "entonces no fueron removidos.".format(
                    successful, len(to_unblacklist) - successful
                ),
                parse_mode=ParseMode.HTML,
            )
    else:
        send_message(
            update.effective_message,
            "Dime qué palabras te gustaría eliminar de la lista negra.!",
        )


@loggable
@user_admin
@typing_action
def blacklist_mode(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
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
                "Este comando solo se puede usar en grupo, no en PM",
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() in ["off", "nothing", "no"]:
            settypeblacklist = "do nothing"
            sql.set_blacklist_strength(chat_id, 0, "0")
        elif args[0].lower() in ["del", "delete"]:
            settypeblacklist = "delete blacklisted message"
            sql.set_blacklist_strength(chat_id, 1, "0")
        elif args[0].lower() == "warn":
            settypeblacklist = "warn the sender"
            sql.set_blacklist_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeblacklist = "mute the sender"
            sql.set_blacklist_strength(chat_id, 3, "0")
        elif args[0].lower() == "kick":
            settypeblacklist = "kick the sender"
            sql.set_blacklist_strength(chat_id, 4, "0")
        elif args[0].lower() == "ban":
            settypeblacklist = "ban the sender"
            sql.set_blacklist_strength(chat_id, 5, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = """Parece que intentó establecer el valor de tiempo para la lista negra pero no especificó el tiempo; Pruebe, `/ blacklistmode tban <valor de tiempo>`.

Ejemplos de valor de tiempo: 4m = 4 minutos, 3h = 3 horas, 6d = 6 días, 5w = 5 semanas."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                teks = """Valor de tiempo no válido!
Ejemplos de valor de tiempo: 4m = 4 minutos, 3h = 3 horas, 6d = 6 días, 5w = 5 semanas."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            settypeblacklist = "temporalmente prohibido por {}".format(args[1])
            sql.set_blacklist_strength(chat_id, 6, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = """Parece que intentó establecer el valor de tiempo para la lista negra pero no especificó el tiempo; Pruebe, `/ blacklistmode tban <valor de tiempo>`.

Ejemplos de valor de tiempo: 4m = 4 minutos, 3h = 3 horas, 6d = 6 días, 5w = 5 semanas."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                teks = """Valor de tiempo no válido!
Ejemplos de valor de tiempo: 4m = 4 minutos, 3h = 3 horas, 6d = 6 días, 5w = 5 semanas."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            settypeblacklist = "Temporalmente silenciado por {}".format(args[1])
            sql.set_blacklist_strength(chat_id, 7, str(args[1]))
        else:
            send_message(
                update.effective_message,
                "Solo entiendo: off/del/warn/ban/kick/mute/tban/tmute!",
            )
            return ""
        if conn:
            text = "Modo de lista negra cambiado: `{}` en *{}*!".format(
                settypeblacklist, chat_name
            )
        else:
            text = "Modo de lista negra cambiado: `{}`!".format(settypeblacklist)
        send_message(update.effective_message, text, parse_mode="markdown")
        return (
            "<b>{}:</b>\n"
            "<b>Admin:</b> {}\n"
            "Cambió el modo de lista negra. voluntad {}.".format(
                html.escape(chat.title),
                mention_html(user.id, html.escape(user.first_name)),
                settypeblacklist,
            )
        )
    else:
        getmode, getvalue = sql.get_blacklist_setting(chat.id)
        if getmode == 0:
            settypeblacklist = "do nothing"
        elif getmode == 1:
            settypeblacklist = "delete"
        elif getmode == 2:
            settypeblacklist = "warn"
        elif getmode == 3:
            settypeblacklist = "mute"
        elif getmode == 4:
            settypeblacklist = "kick"
        elif getmode == 5:
            settypeblacklist = "ban"
        elif getmode == 6:
            settypeblacklist = "temporarily ban for {}".format(getvalue)
        elif getmode == 7:
            settypeblacklist = "temporarily mute for {}".format(getvalue)
        if conn:
            text = "Modo de lista negra actual: *{}* en *{}*.".format(
                settypeblacklist, chat_name
            )
        else:
            text = "Modo de lista negra actual: *{}*.".format(settypeblacklist)
        send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
    return ""


def findall(p, s):
    i = s.find(p)
    while i != -1:
        yield i
        i = s.find(p, i + 1)


@user_not_admin
def del_blacklist(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    bot = context.bot
    to_match = extract_text(message)
    if not to_match:
        return
    if is_approved(chat.id, user.id):
        return
    getmode, value = sql.get_blacklist_setting(chat.id)

    chat_filters = sql.get_chat_blacklist(chat.id)
    for trigger in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(trigger) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            try:
                if getmode == 0:
                    return
                elif getmode == 1:
                    try:
                        message.delete()
                    except BadRequest:
                        pass
                elif getmode == 2:
                    try:
                        message.delete()
                    except BadRequest:
                        pass
                    warn(
                        update.effective_user,
                        chat,
                        ("Usando un disparador en la lista negra: {}".format(trigger)),
                        message,
                        update.effective_user,
                    )
                    return
                elif getmode == 3:
                    message.delete()
                    bot.restrict_chat_member(
                        chat.id,
                        update.effective_user.id,
                        permissions=ChatPermissions(can_send_messages=False),
                    )
                    bot.sendMessage(
                        chat.id,
                        f"Silenciado {user.first_name} por usar una palabra incluida en la lista negra: {trigger}!",
                    )
                    return
                elif getmode == 4:
                    message.delete()
                    res = chat.unban_member(update.effective_user.id)
                    if res:
                        bot.sendMessage(
                            chat.id,
                            f"Expulsado {user.first_name} por usar una palabra incluida en la lista negra: {trigger}!",
                        )
                    return
                elif getmode == 5:
                    message.delete()
                    chat.kick_member(user.id)
                    bot.sendMessage(
                        chat.id,
                        f"Prohibido {user.first_name} por usar una palabra incluida en la lista negra: {trigger}",
                    )
                    return
                elif getmode == 6:
                    message.delete()
                    bantime = extract_time(message, value)
                    chat.kick_member(user.id, until_date=bantime)
                    bot.sendMessage(
                        chat.id,
                        f"Prohibido {user.first_name} hasta '{value}' por usar una palabra incluida en la lista negra: {trigger}!",
                    )
                    return
                elif getmode == 7:
                    message.delete()
                    mutetime = extract_time(message, value)
                    bot.restrict_chat_member(
                        chat.id,
                        user.id,
                        until_date=mutetime,
                        permissions=ChatPermissions(can_send_messages=False),
                    )
                    bot.sendMessage(
                        chat.id,
                        f"Silenciado {user.first_name} hasta '{value}' por usar una palabra incluida en la lista negra: {trigger}!",
                    )
                    return
            except BadRequest as excp:
                if excp.message != "Mensaje para eliminar no encontrado":
                    LOGGER.exception("Error al eliminar el mensaje de la lista negra.")
            break


def __import_data__(chat_id, data):
    # set chat blacklist
    blacklist = data.get("blacklist", {})
    for trigger in blacklist:
        sql.add_to_blacklist(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    blacklisted = sql.num_blacklist_chat_filters(chat_id)
    return "Existen {} palabras en la lista negra.".format(blacklisted)


def __stats__():
    return "• {} activadores de lista negra, en {} chats.".format(
        sql.num_blacklist_filters(), sql.num_blacklist_filter_chats()
    )


__mod_name__ = "Lista-negra"

__help__ = """

Las listas negras se utilizan para evitar que ciertos factores desencadenantes se digan en un grupo. Cada vez que se menciona el desencadenante, el mensaje se eliminará de inmediato. ¡Una buena combinación es a veces combinar esto con filtros de advertencia!

*NOTA*: Las listas negras no afectan a los administradores de grupo.

 • `/blacklist`*:* Ver las palabras actuales de la lista negra.

Solo Administradores:
 • `/addblacklist <desencadenantes>`*:* Agrega un disparador a la lista negra. Cada línea se considera un disparador, por lo que el uso de diferentes líneas le permitirá agregar varios disparadores..
 • `/unblacklist <desencadenantes>`*:* Elimina los desencadenantes de la lista negra. Aquí se aplica la misma lógica de nueva línea, por lo que puede eliminar varios activadores a la vez.
 • `/blacklistmode <off/del/warn/ban/kick/mute/tban/tmute>`*:* Acción a realizar cuando alguien envía palabras de la lista negra.

La etiqueta de lista negra se utiliza para detener ciertas etiquetas. Siempre que se envíe una pegatina, el mensaje se eliminará de inmediato.
*NOTA:* Las pegatinas de la lista negra no afectan al administrador del grupo
 • `/blsticker`*:* Ver la pegatina actual incluida en la lista negra
*Solo Adminisradores:*
 • `/addblsticker <sticker link>`*:* Agregue el disparador de la etiqueta engomada a la lista negra. Se puede agregar a través de la etiqueta de respuesta
 • `/unblsticker <sticker link>`*:* Elimina los desencadenantes de la lista negra. Aquí se aplica la misma lógica de nueva línea, por lo que puede eliminar varios activadores a la vez
 • `/rmblsticker <sticker link>`*:* Lo mismo que arriba
 • `/blstickermode <delete/ban/tban/mute/tmute>`*:* establece una acción predeterminada sobre qué hacer si los usuarios usan pegatinas en la lista negra
Nota:
 • `<enlace de pegatina> `puede ser` https://t.me/addstickers/ <sticker> `o simplemente` <sticker> `o responder al mensaje de la pegatina

"""
BLACKLIST_HANDLER = DisableAbleCommandHandler(
    "blacklist", blacklist, admin_ok=True, run_async=True
)
ADD_BLACKLIST_HANDLER = CommandHandler("addblacklist", add_blacklist, run_async=True)
UNBLACKLIST_HANDLER = CommandHandler("unblacklist", unblacklist, run_async=True)
BLACKLISTMODE_HANDLER = CommandHandler("blacklistmode", blacklist_mode, run_async=True)
BLACKLIST_DEL_HANDLER = MessageHandler(
    (Filters.text | Filters.command | Filters.sticker | Filters.photo) & Filters.chat_type.groups,
    del_blacklist,
    allow_edit=True,
    run_async=True,
)

dispatcher.add_handler(BLACKLIST_HANDLER)
dispatcher.add_handler(ADD_BLACKLIST_HANDLER)
dispatcher.add_handler(UNBLACKLIST_HANDLER)
dispatcher.add_handler(BLACKLISTMODE_HANDLER)
dispatcher.add_handler(BLACKLIST_DEL_HANDLER, group=BLACKLIST_GROUP)

__handlers__ = [
    BLACKLIST_HANDLER,
    ADD_BLACKLIST_HANDLER,
    UNBLACKLIST_HANDLER,
    BLACKLISTMODE_HANDLER,
    (BLACKLIST_DEL_HANDLER, BLACKLIST_GROUP),
]
