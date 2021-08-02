from HunterAlpha import dispatcher
from HunterAlpha.modules.helper_funcs.chat_status import (
    bot_admin,
    is_bot_admin,
    is_user_ban_protected,
    is_user_in_chat,
)
from HunterAlpha.modules.helper_funcs.extraction import extract_user_and_text
from HunterAlpha.modules.helper_funcs.filters import CustomFilters
from telegram import Update, ChatPermissions
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, run_async

RBAN_ERRORS = {
    "El usuario es administrador del chat.",
    "Chat no encontrado",
    "No hay suficientes derechos para restringir / no restringir un miembro del chat",
    "Usuario_no_participante",
    "Peer_id_invalid",
    "Se desactivó el chat grupal",
    "Necesita invitar a un usuario para marcarlo de un grupo básico",
    "Chat_admin_required",
    "Solo el creador de un grupo básico puede marcar a los administradores del grupo",
    "Channel_private",
    "No en el chat",
}

RUNBAN_ERRORS = {
    "El usuario es administrador del chat.",
    "Chat no encontrado",
    "No hay suficientes derechos para restringir / no restringir un miembro del chat",
    "Usuario_no_participante",
    "Peer_id_invalid",
    "Se desactivó el chat grupal",
    "Necesita invitar a un usuario para marcarlo de un grupo básico",
    "Chat_admin_required",
    "Solo el creador de un grupo básico puede marcar a los administradores del grupo",
    "Channel_private",
    "No en el chat",
}

RKICK_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to punch it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can punch group administrators",
    "Channel_private",
    "Not in the chat",
}

RMUTE_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to punch it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can punch group administrators",
    "Channel_private",
    "Not in the chat",
}

RUNMUTE_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to punch it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can punch group administrators",
    "Channel_private",
    "Not in the chat",
}


@bot_admin
def rban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Parece que no te refieres a un chat/usuario.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "Parece que no se está refiriendo a un usuario o el ID especificado es incorrecto.."
        )
        return
    elif not chat_id:
        message.reply_text("No parece que te refieras a un chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat no encontrado":
            message.reply_text(
                "¡Chat no encontrado! Asegúrate de haber ingresado un ID de chat válido y yo soy parte de ese chat."
            )
            return
        else:
            raise

    if chat.type == "private":
        message.reply_text("Lo siento, pero eso es un chat privado!")
        return

    if (
        not is_bot_admin(chat, bot.id)
        or not chat.get_member(bot.id).can_restrict_members
    ):
        message.reply_text(
            "¡No puedo restringir a la gente allí! Asegúrate de que soy administrador y puedo prohibir a los usuarios."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Realmente desearía poder prohibir a los administradores...")
        return

    if user_id == bot.id:
        message.reply_text("Yo no voy a PROHIBIR, estás loco?")
        return

    try:
        chat.kick_member(user_id)
        message.reply_text("Prohibido del chat!")
    except BadRequest as excp:
        if excp.message == "Mensaje de respuesta no encontrado":
            # Do not reply
            message.reply_text("Prohibido!", quote=False)
        elif excp.message in RBAN_ERRORS:
            message.reply_text(excp.message)
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


@bot_admin
def runban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Parece que no te refieres a un chat/usuario.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "Parece que no se está refiriendo a un usuario o el ID especificado es incorrecto.."
        )
        return
    elif not chat_id:
        message.reply_text("No parece que te refieras a un chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat no encontrado":
            message.reply_text(
                "¡Chat no encontrado! Asegúrate de haber ingresado un ID de chat válido y yo soy parte de ese chat."
            )
            return
        else:
            raise

    if chat.type == "private":
        message.reply_text("Lo siento, pero eso es un chat privado!")
        return

    if (
        not is_bot_admin(chat, bot.id)
        or not chat.get_member(bot.id).can_restrict_members
    ):
        message.reply_text(
            "No puedo dejar de restringir a las personas allí! Asegúrate de que soy administrador y puedo desbloquear a los usuarios."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario allí")
            return
        else:
            raise

    if is_user_in_chat(chat, user_id):
        message.reply_text(
            "¿Por qué intentas desbancar de forma remota a alguien que ya está en ese chat??"
        )
        return

    if user_id == bot.id:
        message.reply_text("No voy a DESBANEARME, soy administrador allí!")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Sí, este usuario puede unirse a ese chat.!")
    except BadRequest as excp:
        if excp.message == "Mensaje de respuesta no encontrado":
            # Do not reply
            message.reply_text("No prohibido!", quote=False)
        elif excp.message in RUNBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR desbanning al usuario %s en el chat %s (%s) debido a %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Bueno, maldita sea, no puedo desbancar a ese usuario.")


@bot_admin
def rkick(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Parece que no te refieres a un chat/usuario.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "Parece que no se está refiriendo a un usuario o el ID especificado es incorrecto.."
        )
        return
    elif not chat_id:
        message.reply_text("No parece que te refieras a un chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat no encontrado":
            message.reply_text(
                "¡Chat no encontrado! Asegúrate de haber ingresado un ID de chat válido y yo soy parte de ese chat."
            )
            return
        else:
            raise

    if chat.type == "private":
        message.reply_text("Lo siento, pero eso es un chat privado!")
        return

    if (
        not is_bot_admin(chat, bot.id)
        or not chat.get_member(bot.id).can_restrict_members
    ):
        message.reply_text(
            "¡No puedo restringir a la gente allí! Asegúrate de que soy administrador y puedo marcar a los usuarios."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Realmente desearía poder golpear a los administradores...")
        return

    if user_id == bot.id:
        message.reply_text("No me voy a golpear, ¿estás loco??")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Golpeado desde el chat!")
    except BadRequest as excp:
        if excp.message == "Mensaje de respuesta no encontrado":
            # Do not reply
            message.reply_text("Perforado!", quote=False)
        elif excp.message in RKICK_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR perforando usuario %s en el chat %s (%s) debido a %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Bueno maldita sea, no puedo golpear a ese usuario.")


@bot_admin
def rmute(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Parece que no te refieres a un chat/usuario.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "Parece que no se está refiriendo a un usuario o el ID especificado es incorrecto.."
        )
        return
    elif not chat_id:
        message.reply_text("No parece que te refieras a un chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat no encontrado":
            message.reply_text(
                "¡Chat no encontrado! Asegúrate de haber ingresado un ID de chat válido y yo soy parte de ese chat."
            )
            return
        else:
            raise

    if chat.type == "private":
        message.reply_text("Lo siento, pero eso es un chat privado!")
        return

    if (
        not is_bot_admin(chat, bot.id)
        or not chat.get_member(bot.id).can_restrict_members
    ):
        message.reply_text(
            "¡No puedo restringir a la gente allí! Asegúrate de que soy administrador y puedo silenciar a los usuarios."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Realmente desearía poder silenciar a los administradores...")
        return

    if user_id == bot.id:
        message.reply_text("No me voy a enmudecer, ¿estás loco??")
        return

    try:
        bot.restrict_chat_member(
            chat.id, user_id, permissions=ChatPermissions(can_send_messages=False)
        )
        message.reply_text("Silenciado del chat!")
    except BadRequest as excp:
        if excp.message == "Mensaje de respuesta no encontrado":
            # Do not reply
            message.reply_text("Silenciado!", quote=False)
        elif excp.message in RMUTE_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR silenciando a usuario %s en el chat %s (%s) debido a %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Bueno maldita sea, no puedo silenciar a ese usuario.")


@bot_admin
def runmute(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        message.reply_text("Parece que no te refieres a un chat/usuario.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "Parece que no se está refiriendo a un usuario o el ID especificado es incorrecto.."
        )
        return
    elif not chat_id:
        message.reply_text("No parece que te refieras a un chat.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat no encontrado":
            message.reply_text(
                "¡Chat no encontrado! Asegúrate de haber ingresado un ID de chat válido y yo soy parte de ese chat."
            )
            return
        else:
            raise

    if chat.type == "private":
        message.reply_text("Lo siento, pero eso es un chat privado!")
        return

    if (
        not is_bot_admin(chat, bot.id)
        or not chat.get_member(bot.id).can_restrict_members
    ):
        message.reply_text(
            "¡No puedo dejar de restringir a las personas allí! Asegúrate de que soy administrador y puedo desbloquear a los usuarios."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario allí")
            return
        else:
            raise

    if is_user_in_chat(chat, user_id):
        if (
            member.can_send_messages
            and member.can_send_media_messages
            and member.can_send_other_messages
            and member.can_add_web_page_previews
        ):
            message.reply_text("Este usuario ya tiene derecho a hablar en ese chat..")
            return

    if user_id == bot.id:
        message.reply_text("No voy a DESMUTEARME, soy un administrador allí!")
        return

    try:
        bot.restrict_chat_member(
            chat.id,
            int(user_id),
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        message.reply_text("Sí, este usuario puede hablar en ese chat.!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("No silenciado!", quote=False)
        elif excp.message in RUNMUTE_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR usuario anulando %s en el chat %s (%s) debido a %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Bueno maldita sea, no puedo silenciar a ese usuario.")


RBAN_HANDLER = CommandHandler("rban", rban, filters=CustomFilters.sudo_filter, run_async=True)
RUNBAN_HANDLER = CommandHandler("runban", runban, filters=CustomFilters.sudo_filter, run_async=True)
RKICK_HANDLER = CommandHandler("rpunch", rkick, filters=CustomFilters.sudo_filter, run_async=True)
RMUTE_HANDLER = CommandHandler("rmute", rmute, filters=CustomFilters.sudo_filter, run_async=True)
RUNMUTE_HANDLER = CommandHandler("runmute", runmute, filters=CustomFilters.sudo_filter, run_async=True)

dispatcher.add_handler(RBAN_HANDLER)
dispatcher.add_handler(RUNBAN_HANDLER)
dispatcher.add_handler(RKICK_HANDLER)
dispatcher.add_handler(RMUTE_HANDLER)
dispatcher.add_handler(RUNMUTE_HANDLER)
