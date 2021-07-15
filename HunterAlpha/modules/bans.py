import html

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

from HunterAlpha import (
    DEV_USERS,
    LOGGER,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    WHITELIST_USERS,
    dispatcher,
)
from HunterAlpha.modules.disable import DisableAbleCommandHandler
from HunterAlpha.modules.helper_funcs.chat_status import (
    bot_admin,
    can_restrict,
    connection_status,
    is_user_admin,
    is_user_ban_protected,
    is_user_in_chat,
    user_admin,
    user_can_ban,
    can_delete,
)
from HunterAlpha.modules.helper_funcs.extraction import extract_user_and_text
from HunterAlpha.modules.helper_funcs.string_handling import extract_time
from HunterAlpha.modules.log_channel import gloggable, loggable


@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot = context.bot
    args = context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dudo que sea un usuario.")
        return log_message
    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "Usuario no encontrado":
            raise
        message.reply_text("Parece que no puedo encontrar a esta persona.")
        return log_message
    if user_id == bot.id:
        message.reply_text("Oh sí, banéame, novato!")
        return log_message

    if is_user_ban_protected(chat, user_id, member) and user not in DEV_USERS:
        if user_id == OWNER_ID:
            message.reply_text("Tratando de ponerme en contra de Dios eh?")
        elif user_id in DEV_USERS:
            message.reply_text("No puedo actuar contra el nuestro.")
        elif user_id in SUDO_USERS:
            message.reply_text(
                "Luchar contra este usuario de sudo aquí pondrá en riesgo la vida de los usuarios."
            )
        elif user_id in SUPPORT_USERS:
            message.reply_text("Traiga un usuario desarrollador para luchar contra un usuario de soporte.")
        elif user_id in WHITELIST_USERS:
            message.reply_text("Los usuarios de la lista blanca no pueden ser prohibidos.")
        else:
            message.reply_text("Este usuario tiene inmunidad y no puede ser prohibido..")
        return log_message
    if message.text.startswith("/s"):
        silent = True
        if not can_delete(chat, context.bot.id):
            return ""
    else:
        silent = False
    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#{'S' if silent else ''}BANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += "\n<b>Razon:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)

        if silent:
            if message.reply_to_message:
                message.reply_to_message.delete()
            message.delete()
            return log

        reply = (
            f"<code>❕</code><b>Ban Event</b>\n"
            f"<code> </code><b>•  User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            reply += f"\n<code> </code><b>•  Razon:</b> \n{html.escape(reason)}"
        bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML,)
        return log

    except BadRequest as excp:
        if excp.message == "Mensaje de respuesta no encontrado":
            # Do not reply
            if silent:
                return log
            message.reply_text("Prohibido!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR prohibir al usuario %s en el chat %s (%s) debido a %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Uhm ... eso no funcionó...")

    return log_message


@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def temp_ban(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dudo que sea un usuario.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "Usuario no encontrado":
            raise
        message.reply_text("Parece que no puedo encontrar a este usuario.")
        return log_message
    if user_id == bot.id:
        message.reply_text("Yo no lo voy a PROHIBIR, estás loco?")
        return log_message

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("No me apetece.")
        return log_message

    if not reason:
        message.reply_text("No has especificado un momento para prohibir a este usuario.!")
        return log_message

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    bantime = extract_time(message, time_val)

    if not bantime:
        return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        "#TEMP BANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
        f"<b>Time:</b> {time_val}"
    )
    if reason:
        log += "\n<b>Razon:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.sendMessage(
            chat.id,
            f"¡Prohibido! Usuario {mention_html(member.user.id, html.escape(member.user.first_name))} "
            f"será prohibido por {time_val}.",
            parse_mode=ParseMode.HTML,
        )
        return log

    except BadRequest as excp:
        if excp.message == "Mensaje de respuesta no encontrado":
            # Do not reply
            message.reply_text(
                f"¡Prohibido! El usuario será baneado por {time_val}.", quote=False
            )
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR al prohibir al usuario %s en el chat %s (%s) debido a %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Bueno maldita sea, no puedo prohibir a ese usuario.")

    return log_message


@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def punch(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dudo que sea un usuario.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "Usuario no encontrado":
            raise

        message.reply_text("Parece que no puedo encontrar a este usuario.")
        return log_message
    if user_id == bot.id:
        message.reply_text("Yeahhh no voy a hacer eso.")
        return log_message

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Realmente desearía poder golpear a este usuario....")
        return log_message

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        reply = (
            f"<code>❕</code><b>Evento de puñetazo</b>\n"
            f"<code> </code><b>•  User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
        )
        if reason:
            reply += f"<code> </code><b>•  Razon:</b> {html.escape(reason)}"
        bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML
        )
        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#KICKED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            log += f"\n<b>Razon:</b> {reason}"

        return log

    else:
        message.reply_text("Bueno maldita sea, no puedo golpear a ese usuario.")

    return log_message


@bot_admin
@can_restrict
def punchme(update: Update, context: CallbackContext):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Desearía poder ... pero eres un administrador.")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("Te saca del grupo")
    else:
        update.effective_message.reply_text("Eh? No puedo :/")


@connection_status
@bot_admin
@can_restrict
@user_admin
@user_can_ban
@loggable
def unban(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dudo que sea un usuario.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "Usuario no encontrado":
            raise
        message.reply_text("Parece que no puedo encontrar a este usuario.")
        return log_message
    if user_id == bot.id:
        message.reply_text("Cómo me desharía de la prohibición si no estuviera aquí?...?")
        return log_message

    if is_user_in_chat(chat, user_id):
        message.reply_text("No está esta persona ya aquí???")
        return log_message

    chat.unban_member(user_id)
    message.reply_text("Sí, este usuario puede unirse.?!")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += f"\n<b>Razon:</b> {reason}"

    return log


@connection_status
@bot_admin
@can_restrict
@gloggable
def selfunban(context: CallbackContext, update: Update) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    if user.id not in SUDO_USERS:
        return

    try:
        chat_id = int(args[0])
    except:
        message.reply_text("Dar una identificación de chat válida.")
        return

    chat = bot.getChat(chat_id)

    try:
        member = chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario.")
            return
        else:
            raise

    if is_user_in_chat(chat, user.id):
        message.reply_text("No estás ya en el chat???")
        return

    chat.unban_member(user.id)
    message.reply_text("Sí, te he quitado la prohibición.")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )

    return log


__help__ = """
 • `/punchme`*:* Golpea al usuario que emitió el comando.
 • `/kickme`*:* Lo mismo que punchme

*Admins only:*
 • `/ban <usuario>`*:* prohíbe a un usuario. (a través del id o respuesta)
 • `/sban <usuario>`*:* Prohibir silenciosamente a un usuario. Elimina comando, mensaje respondido y no responde. (a través del id o respuesta)
 • `/tban <usuario> x(m/h/d)`*:* prohíbe a un usuario por tiempo `x`. (a través del id o respuesta). `m` =` minutos`, `h` =` horas`, `d` =` días`.
 • `/unban <usuario>`*:* anula la prohibición de un usuario. (a través del id o respuesta)
 • `/punch <usuario> <razon>(opcional)`*:* Saca a un usuario del grupo (mediante el id o la respuesta)
 • `/kick <usuario>`*:* Lo mismo que punch
"""

BAN_HANDLER = DisableAbleCommandHandler(["ban", "sban"], ban, run_async=True)
TEMPBAN_HANDLER = DisableAbleCommandHandler("tban", temp_ban, run_async=True)
PUNCH_HANDLER = DisableAbleCommandHandler(["punch", "kick"], punch, run_async=True)
UNBAN_HANDLER = DisableAbleCommandHandler("unban", unban, run_async=True)
ROAR_HANDLER = DisableAbleCommandHandler("roar", selfunban, run_async=True)
PUNCHME_HANDLER = DisableAbleCommandHandler(["punchme", "kickme"], punchme, filters=Filters.chat_type.groups, run_async=True)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(PUNCH_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(ROAR_HANDLER)
dispatcher.add_handler(PUNCHME_HANDLER)

__mod_name__ = "Prohibiciones"
__handlers__ = [
    BAN_HANDLER,
    TEMPBAN_HANDLER,
    PUNCH_HANDLER,
    UNBAN_HANDLER,
    ROAR_HANDLER,
    PUNCHME_HANDLER,
]
