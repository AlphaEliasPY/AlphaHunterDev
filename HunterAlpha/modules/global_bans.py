import html
import time
from datetime import datetime
from io import BytesIO

from telegram import ParseMode, Update
from telegram.error import BadRequest, TelegramError, Unauthorized
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)
from telegram.utils.helpers import mention_html

import HunterAlpha.modules.sql.global_bans_sql as sql
from HunterAlpha.modules.sql.users_sql import get_user_com_chats
from HunterAlpha import (
    DEV_USERS,
    EVENT_LOGS,
    OWNER_ID,
    STRICT_GBAN,
    SUDO_USERS,
    SUPPORT_CHAT,
    SPAMWATCH_SUPPORT_CHAT,
    SUPPORT_USERS,
    WHITELIST_USERS,
    sw,
    dispatcher,
)
from HunterAlpha.modules.helper_funcs.chat_status import (
    is_user_admin,
    support_plus,
    user_admin,
)
from HunterAlpha.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from HunterAlpha.modules.helper_funcs.misc import send_to_list

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "El usuario es administrador del chat.",
    "Chat no encontrado",
    "No hay suficientes derechos para restringir / no restringir un miembro del chat",
    "Usuario_no_participante",
    "Peer_id_invalid",
    "Se desactivó el chat grupal",
    "Necesita invitar a un usuario para sacarlo de un grupo básico",
    "Chat_admin_required",
    "Solo el creador de un grupo básico puede expulsar a los administradores del grupo",
    "Channel_private",
    "No en el chat",
    "No se puede eliminar al propietario del chat",
}

UNGBAN_ERRORS = {
    "El usuario es administrador del chat.",
    "Chat no encontrado",
    "No hay suficientes derechos para restringir / no restringir un miembro del chat",
    "Usuario_no_participante",
    "El método está disponible solo para chats de canal y supergrupo",
    "No en el chat",
    "Channel_private",
    "Chat_admin_required",
    "Peer_id_invalid",
    "Usuario no encontrado",
}


@support_plus
def gban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "Parece que no se está refiriendo a un usuario o el ID especificado es incorrecto.."
        )
        return

    if int(user_id) in DEV_USERS:
        message.reply_text("Este es un usuario desarrollador\nNo puedo actuar contra el nuestro.")
        return

    if int(user_id) in SUDO_USERS:
        message.reply_text(
            "Yo espío, con mi ojito ... ¡un usuario de sudo! ¿Por qué se están volviendo el uno contra el otro??"
        )
        return

    if int(user_id) in SUPPORT_USERS:
        message.reply_text(
            "¡OOOH alguien está tratando de gban a un usuario de soporte! *agarra palomitas de maíz*"
        )
        return

    if int(user_id) in WHITELIST_USERS:
        message.reply_text("Eso es un usuario de la lista blanca! No pueden ser prohibidos!")
        return

    if user_id == bot.id:
        message.reply_text("Tu uhh ... quieres que me golpee?")
        return

    if user_id in [777000, 1087968824]:
        message.reply_text("¡Tonto! No puedes atacar la tecnología nativa de Telegram!")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario.")
            return ""
        else:
            return

    if user_chat.type != "private":
        message.reply_text("Eso no es un usuario!")
        return

    if sql.is_user_gbanned(user_id):

        if not reason:
            message.reply_text(
                "Este usuario ya está gbanned; Cambiaría el motivo, pero no me has dado uno..."
            )
            return

        old_reason = sql.update_gban_reason(
            user_id, user_chat.username or user_chat.first_name, reason
        )
        if old_reason:
            message.reply_text(
                "Este usuario ya está gbanned por el siguiente motivo:\n"
                "<code>{}</code>\n"
                "Lo he actualizado con tu nueva razón!".format(
                    html.escape(old_reason)
                
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            message.reply_text(
                "Este usuario ya está gbanned, pero no se ha establecido ningún motivo; Me fui y lo actualicé!"
            )

        return

    message.reply_text("On it!")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != "private":
        chat_origin = "<b>{} ({})</b>\n".format(html.escape(chat.title), chat.id)
    else:
        chat_origin = "<b>{}</b>\n".format(chat.id)

    log_message = (
        f"#GBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Banned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Banned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>"
    )

    if reason:
        if chat.type == chat.SUPERGROUP and chat.username:
            log_message += f'\n<b>Reason:</b> <a href="https://telegram.me/{chat.username}/{message.message_id}">{reason}</a>'
        else:
            log_message += f"\n<b>Reason:</b> <code>{reason}</code>"

    if EVENT_LOGS:
        try:
            log = bot.send_message(EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                EVENT_LOGS,
                log_message
                + "\n\nFormatting has been disabled due to an unexpected error.",
            )

    else:
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log_message, html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_user_com_chats(user_id)
    gbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
            gbanned_chats += 1

        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text(f"No se pudo gban debido a: {excp.message}")
                if EVENT_LOGS:
                    bot.send_message(
                        EVENT_LOGS,
                        f"No se pudo gban debido a {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    send_to_list(
                        bot, SUDO_USERS + SUPPORT_USERS, f"No se pudo gban debido a: {excp.message}"
                    )
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    if EVENT_LOGS:
        log.edit_text(
            log_message + f"\n<b>Chats affected:</b> <code>{gbanned_chats}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        send_to_list(
            bot,
            SUDO_USERS + SUPPORT_USERS,
            f"Gban completo! (Usuario prohibido en <code>{gbanned_chats}</code> chats)",
            html=True,
        )

    end_time = time.time()
    gban_time = round((end_time - start_time), 2)

    if gban_time > 60:
        gban_time = round((gban_time / 60), 2)
        message.reply_text("¡Hecho! Gbanned.", parse_mode=ParseMode.HTML)
    else:
        message.reply_text("¡Hecho! Gbanned.", parse_mode=ParseMode.HTML)

    try:
        bot.send_message(
            user_id,
            "#EVENT"
            "Se le marcó como malicioso y, como tal, se le prohibió participar en los grupos que administramos en el futuro.."
            f"\n<b>Razon:</b> <code>{html.escape(user.reason)}</code>"
            f"</b>Chat de apelación:</b> @{SUPPORT_CHAT}",
            parse_mode=ParseMode.HTML,
        )
    except:
        pass  # bot probably blocked by user


@support_plus
def ungban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "Parece que no se está refiriendo a un usuario o el ID especificado es incorrecto.."
        )
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != "private":
        message.reply_text("Eso no es un usuario!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("Este usuario no está prohibido!")
        return

    message.reply_text(f"daré {user_chat.first_name} una segunda oportunidad, a nivel mundial.")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != "private":
        chat_origin = f"<b>{html.escape(chat.title)} ({chat.id})</b>\n"
    else:
        chat_origin = f"<b>{chat.id}</b>\n"

    log_message = (
        f"#UNGBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Unbanned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Unbanned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>"
    )

    if EVENT_LOGS:
        try:
            log = bot.send_message(EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                EVENT_LOGS,
                log_message
                + "\n\nEl formateo se ha deshabilitado debido a un error inesperado.",
            )
    else:
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log_message, html=True)

    chats = get_user_com_chats(user_id)
    ungbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == "kicked":
                bot.unban_chat_member(chat_id, user_id)
                ungbanned_chats += 1

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text(f"No se pudo cancelar la GBAN debido a: {excp.message}")
                if EVENT_LOGS:
                    bot.send_message(
                        EVENT_LOGS,
                        f"No se pudo cancelar la GBAN debido a: {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    bot.send_message(
                        OWNER_ID, f"No se pudo cancelar la GBAN debido a: {excp.message}"
                    )
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    if EVENT_LOGS:
        log.edit_text(
            log_message + f"\n<b>Chats affected:</b> <code>{ungbanned_chats}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "Un-gban completo!")

    end_time = time.time()
    ungban_time = round((end_time - start_time), 2)

    if ungban_time > 60:
        ungban_time = round((ungban_time / 60), 2)
        message.reply_text(f"La persona ha sido eliminada. Tomó {ungban_time} min")
    else:
        message.reply_text(f"La persona ha sido eliminada. Tomó {ungban_time} sec")


@support_plus
def gbanlist(update: Update, context: CallbackContext):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text(
            "No hay usuarios con gbanned! Eres más amable de lo que esperaba..."
        )
        return

    banfile = "Al diablo con estos chicos.\n"
    for user in banned_users:
        banfile += f"[x] {user['name']} - {user['user_id']}\n"
        if user["razon"]:
            banfile += f"Razon: {user['razon']}\n"

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="Aquí está la lista de usuarios gbanned actualmente.",
        )


def check_and_ban(update, user_id, should_message=True):

    if user_id in WHITELIST_USERS:
        sw_ban = None
    else:
        try:
            sw_ban = sw.get_ban(int(user_id))
        except:
            sw_ban = None

    if sw_ban:
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text(
                f"<b>Alert</b>: este usuario está prohibido a nivel mundial.\n"
                f"<code>*Los prohíbe desde aquí*</code>.\n"
                f"<b>Chat de apelación</b>: {SPAMWATCH_SUPPORT_CHAT}\n"
                f"<b>User ID</b>: <code>{sw_ban.id}</code>\n"
                f"<b>Ban Razon</b>: <code>{html.escape(sw_ban.reason)}</code>",
                parse_mode=ParseMode.HTML,
            )
        return

    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            text = (
                f"<b>Alert</b>: este usuario está prohibido a nivel mundial.\n"
                f"<code>*Los prohíbe desde aquí*</code>.\n"
                f"<b>Chat de apelación</b>: @{SUPPORT_CHAT}\n"
                f"<b>User ID</b>: <code>{user_id}</code>"
            )
            user = sql.get_gbanned_user(user_id)
            if user.reason:
                text += f"\n<b>Ban Reason:</b> <code>{html.escape(user.reason)}</code>"
            update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


def enforce_gban(update: Update, context: CallbackContext):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    bot = context.bot
    try:
        restrict_permission = update.effective_chat.get_member(
            bot.id
        ).can_restrict_members
    except Unauthorized:
        return
    if sql.does_chat_gban(update.effective_chat.id) and restrict_permission:
        user = update.effective_user
        chat = update.effective_chat
        msg = update.effective_message

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)
            return

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@user_admin
def gbanstat(update: Update, context: CallbackContext):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "El antispam ahora está habilitado ✅ "
                "Ahora estoy protegiendo a su grupo de posibles amenazas remotas.!"
            )
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "Antispam ahora está deshabilitado ❌ " "Spamwatch ahora está deshabilitado ❌"
            )
    else:
        update.effective_message.reply_text(
            "Dame algunos argumentos para elegir un escenario! on/off, yes/no!\n\n"
            "Tu configuración actual es: {}\n"
            "Cuando es Verdadero, cualquier GBAN que suceda también ocurrirá en su grupo.. "
            "Cuando es falso, no lo harán, dejándote a la posible merced de "
            "spammers.".format(sql.does_chat_gban(update.effective_chat.id))
        )


def __stats__():
    return f"• {sql.num_gbanned_users()} Usuarios prohibidos globalmente."


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)
    text = "Prohibido globalmente: <b>{}</b>"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == dispatcher.bot.id:
        return ""
    if int(user_id) in SUDO_USERS + WHITELIST_USERS:
        return ""
    if is_gbanned:
        text = text.format("Yes")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += f"\n<b>Razon:</b> <code>{html.escape(user.reason)}</code>"
        text += f"\n<b>Chat de apelacion:</b> @{SUPPORT_CHAT}"
    else:
        text = text.format("No")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"Este chat es obligatorio *gbans*: `{sql.does_chat_gban(chat_id)}`."


__help__ = f"""
*Solo administradores:*
 • `/antispam <on/off/yes/no>`*:* Cambiará nuestra tecnología antispam o devolverá su configuración actual.

Anti-Spam, utilizado por los desarrolladores de bots para prohibir a los spammers en todos los grupos. Esto ayuda a proteger \
usted y sus grupos eliminando los flooders de spam lo más rápido posible.
*Nota:* Los usuarios pueden apelar gbans o denunciar spammers en @ {SUPPORT_CHAT}

Esto también integra la API de @Spamwatch para eliminar los spammers tanto como sea posible de su sala de chat!
*¿Qué es SpamWatch?*
SpamWatch mantiene una gran lista de prohibiciones constantemente actualizada de spambots, trolls, spammers de bitcoin y personajes desagradables [.] (Https://telegra.ph/file/f584b643c6f4be0b1de53.jpg)
Ayude constantemente a expulsar a los spammers de su grupo automáticamente. Por lo tanto, no tendrá que preocuparse de que los spammers asalten su grupo.
* Nota: * Los usuarios pueden apelar las prohibiciones de spamwatch en @SpamwatchSupport
"""

GBAN_HANDLER = CommandHandler("gban", gban, run_async=True)
UNGBAN_HANDLER = CommandHandler("ungban", ungban, run_async=True)
GBAN_LIST = CommandHandler("gbanlist", gbanlist, run_async=True)

GBAN_STATUS = CommandHandler("antispam", gbanstat, filters=Filters.chat_type.groups, run_async=True)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.chat_type.groups, enforce_gban, run_async=True)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

__mod_name__ = "Anti-Spam"
__handlers__ = [GBAN_HANDLER, UNGBAN_HANDLER, GBAN_LIST, GBAN_STATUS]

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
    __handlers__.append((GBAN_ENFORCER, GBAN_ENFORCE_GROUP))
