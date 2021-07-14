import html

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

from HunterAlpha import SUDO_USERS, dispatcher
from HunterAlpha.modules.disable import DisableAbleCommandHandler
from HunterAlpha.modules.helper_funcs.chat_status import (
    bot_admin,
    can_pin,
    can_promote,
    connection_status,
    user_admin,
    ADMIN_CACHE,
)

from HunterAlpha.modules.helper_funcs.telethn.admin_rights import (
    user_can_pin,
    user_can_promote,
    user_can_changeinfo,
)

from HunterAlpha.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from HunterAlpha.modules.log_channel import loggable
from HunterAlpha.modules.helper_funcs.alternate import send_message
from HunterAlpha.modules.helper_funcs.alternate import typing_action

@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def promote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    if (
        not (promoter.can_promote_members or promoter.status == "creator")
        and user.id not in SUDO_USERS
    ):
        message.reply_text("No tienes los derechos necesarios para hacer eso!")
        return

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "No parece que se esté refiriendo a un usuario o el ID especificado es incorrecto.."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == "administrator" or user_member.status == "creator":
        message.reply_text("Cómo se supone que debo promocionar a alguien que ya es administrador?")
        return

    if user_id == bot.id:
        message.reply_text("No puedo promocionarme! Consiga un administrador para que lo haga por mí.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            # can_promote_members=bot_member.can_promote_members,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("No puedo promocionar a alguien que no está en el grupo.")
        else:
            message.reply_text("Ocurrió un error al promocionar.")
        return

    bot.sendMessage(
        chat.id,
        f"Promocionado con éxito <b>{user_member.user.first_name or user_id}</b>!",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#PROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def demote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    demoter = chat.get_member(user.id)

    if (
        not (demoter.can_promote_members or demoter.status == "creator")
        and user.id not in SUDO_USERS
    ):
        message.reply_text("No tienes los derechos necesarios para hacer eso!")
        return

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "No parece que se esté refiriendo a un usuario o el ID especificado es incorrecto.."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == "creator":
        message.reply_text("Esta persona CREÓ el chat, ¿cómo la degradaría??")
        return

    if not user_member.status == "administrator":
        message.reply_text("No se puede degradar lo que no se promovió")
        return

    if user_id == bot.id:
        message.reply_text("No puedo degradarme! Consiga un administrador para que lo haga por mí.")
        return

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
        )

        bot.sendMessage(
            chat.id,
            f"Degradado con éxito <b>{user_member.user.first_name or user_id}</b>!",
            parse_mode=ParseMode.HTML,
        )

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#DEMOTED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message
    except BadRequest:
        message.reply_text(
            "No se pudo degradar. Es posible que no sea administrador o que el estado de administrador fue designado por otro"
            " usuario, por lo que no puedo actuar sobre ellos"
        )
        return


@user_admin
def refresh_admin(update, _):
    try:
        ADMIN_CACHE.pop(update.effective_chat.id)
    except KeyError:
        pass

    update.effective_message.reply_text("Caché de administradores actualizado!")


@connection_status
@bot_admin
@can_promote
@user_admin
def set_title(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if not user_id:
        message.reply_text(
            "No parece que se esté refiriendo a un usuario o el ID especificado es incorrecto.."
        )
        return

    if user_member.status == "creator":
        message.reply_text(
            "Esta persona CREÓ el chat, ¿cómo puedo configurar un título personalizado para él?"
        )
        return

    if user_member.status != "administrator":
        message.reply_text(
            "No se puede establecer el título para los no administradores!\nPrimítelos primero para establecer un título personalizado!!"
        )
        return

    if user_id == bot.id:
        message.reply_text(
            "No puedo establecer mi propio título yo mismo! Haz que el que me hizo administrador lo haga por mí."
        )
        return

    if not title:
        message.reply_text("Establecer un título en blanco no hace nada!")
        return

    if len(title) > 16:
        message.reply_text(
            "La longitud del título es superior a 16 caracteres.\nTruncarlo a 16 caracteres."
        )

    try:
        bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
    except BadRequest:
        message.reply_text("O no los promocione yo o estableces un texto de título que es imposible de configurar.")
        return

    bot.sendMessage(
        chat.id,
        f"Se estableció correctamente el título para <code>{user_member.user.first_name or user_id}</code> "
        f"to <code>{html.escape(title[:16])}</code>!",
        parse_mode=ParseMode.HTML,
    )


@bot_admin
@user_admin
@typing_action
def setchatpic(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Falta el derecho a cambiar la información del grupo!")
        return

    if msg.reply_to_message:
        if msg.reply_to_message.photo:
            pic_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            pic_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("Solo puedes configurar alguna foto como imagen de chat!")
            return
        dlmsg = msg.reply_text("Solo un segundo...")
        tpic = context.bot.get_file(pic_id)
        tpic.download("gpic.png")
        try:
            with open("gpic.png", "rb") as chatp:
                context.bot.set_chat_photo(int(chat.id), photo=chatp)
                msg.reply_text("Establecer con éxito nuevo chatpic!")
        except BadRequest as excp:
            msg.reply_text(f"Error! {excp.message}")
        finally:
            dlmsg.delete()
            if os.path.isfile("gpic.png"):
                os.remove("gpic.png")
    else:
        msg.reply_text("Responder a alguna foto o archivo para establecer una nueva imagen de chat!")


@bot_admin
@user_admin
@typing_action
def rmchatpic(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("No tienes suficientes derechos para eliminar la foto de grupo")
        return
    try:
        context.bot.delete_chat_photo(int(chat.id))
        msg.reply_text("La foto de perfil del chat se eliminó correctamente!")
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")
        return


@bot_admin
@user_admin
@typing_action
def setchat_title(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    args = context.args

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("No tienes suficientes derechos para cambiar la información del chat!")
        return

    title = " ".join(args)
    if not title:
        msg.reply_text("Ingrese un poco de texto para establecer un nuevo título en su chat!")
        return

    try:
        context.bot.set_chat_title(int(chat.id), str(title))
        msg.reply_text(
            f"Establecido con éxito <b>{title}</b> como nuevo título de chat!",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")
        return


@bot_admin
@user_admin
@typing_action
def set_sticker(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text("Te faltan derechos para cambiar la información del chat!")

    if msg.reply_to_message:
        if not msg.reply_to_message.sticker:
            return msg.reply_text(
                "Debes responder a alguna pegatina para configurar el conjunto de pegatinas de chat!"
            )
        stkr = msg.reply_to_message.sticker.set_name
        try:
            context.bot.set_chat_sticker_set(chat.id, stkr)
            msg.reply_text(
                f"Colocó con éxito nuevas pegatinas de grupo {chat.title}!")
        except BadRequest as excp:
            if excp.message == "Participants_too_few":
                return msg.reply_text(
                    "Lo sentimos, debido a las restricciones de telegramas, el chat debe tener un mínimo de 100 miembros antes de que puedan tener pegatinas de grupo!"
                )
            msg.reply_text(f"Error! {excp.message}.")
    else:
        msg.reply_text(
            "Debes responder a alguna pegatina para configurar el conjunto de pegatinas de chat!")


@bot_admin
@user_admin
@typing_action
def set_desc(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text("Te faltan derechos para cambiar la información del chat!")

    tesc = msg.text.split(None, 1)
    if len(tesc) >= 2:
        desc = tesc[1]
    else:
        return msg.reply_text("Establecer una descripción vacía no hará nada!")
    try:
        if len(desc) > 255:
            return msg.reply_text(
                "La descripción debe tener menos de 255 caracteres!")
        context.bot.set_chat_description(chat.id, desc)
        msg.reply_text(
            f"Descripción del chat actualizada con éxito en {chat.title}!")
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")


def __chat_settings__(chat_id, user_id):
    return "Eres *admin*: `{}`".format(
        dispatcher.bot.get_chat_member(chat_id, user_id).status
        in ("administrator", "creator")
    )
    

@bot_admin
@can_pin
@user_admin
@loggable
def pin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    user = update.effective_user
    chat = update.effective_chat

    is_group = chat.type != "private" and chat.type != "channel"
    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (
            args[0].lower() == "notify"
            or args[0].lower() == "loud"
            or args[0].lower() == "violent"
        )

    if prev_message and is_group:
        try:
            bot.pinChatMessage(
                chat.id, prev_message.message_id, disable_notification=is_silent
            )
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#PINNED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )

        return log_message


@bot_admin
@can_pin
@user_admin
@loggable
def unpin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user

    try:
        bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNPINNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
    )

    return log_message


@bot_admin
@user_admin
@connection_status
def invite(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat

    if chat.username:
        update.effective_message.reply_text(f"https://t.me/{chat.username}")
    elif chat.type in [chat.SUPERGROUP, chat.CHANNEL]:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text(
                "No tengo acceso al enlace de invitación, intente cambiar mis permisos!"
            )
    else:
        update.effective_message.reply_text(
            "Solo puedo darte enlaces de invitación para supergrupos y canales, lo siento!"
        )


@connection_status
def adminlist(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    args = context.args
    bot = context.bot

    if update.effective_message.chat.type == "private":
        send_message(update.effective_message, "Este comando solo funciona en grupos.")
        return

    chat = update.effective_chat
    chat_id = update.effective_chat.id
    chat_name = update.effective_message.chat.title

    try:
        msg = update.effective_message.reply_text(
            "Fetching group admins...", parse_mode=ParseMode.HTML
        )
    except BadRequest:
        msg = update.effective_message.reply_text(
            "Fetching group admins...", quote=False, parse_mode=ParseMode.HTML
        )

    administrators = bot.getChatAdministrators(chat_id)
    text = "Administradores en <b>{}</b>:".format(html.escape(update.effective_chat.title))

    bot_admin_list = []

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.first_name == "":
            name = "☠ Cuenta eliminada"
        else:
            name = "{}".format(
                mention_html(
                    user.id, html.escape(user.first_name + " " + (user.last_name or ""))
                )
            )

        if user.is_bot:
            bot_admin_list.append(name)
            administrators.remove(admin)
            continue

        # if user.username:
        #    name = escape_markdown("@" + user.username)
        if status == "creator":
            text += "\n 👑 Creador:"
            text += "\n<code> • </code>{}\n".format(name)

            if custom_title:
                text += f"<code> ┗━ {html.escape(custom_title)}</code>\n"

    text += "\n🔱 Admins:"

    custom_admin_list = {}
    normal_admin_list = []

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.first_name == "":
            name = "☠ Cuenta eliminada"
        else:
            name = "{}".format(
                mention_html(
                    user.id, html.escape(user.first_name + " " + (user.last_name or ""))
                )
            )
        # if user.username:
        #    name = escape_markdown("@" + user.username)
        if status == "administrator":
            if custom_title:
                try:
                    custom_admin_list[custom_title].append(name)
                except KeyError:
                    custom_admin_list.update({custom_title: [name]})
            else:
                normal_admin_list.append(name)

    for admin in normal_admin_list:
        text += "\n<code> • </code>{}".format(admin)

    for admin_group in custom_admin_list.copy():
        if len(custom_admin_list[admin_group]) == 1:
            text += "\n<code> • </code>{} | <code>{}</code>".format(
                custom_admin_list[admin_group][0], html.escape(admin_group)
            )
            custom_admin_list.pop(admin_group)

    text += "\n"
    for admin_group, value in custom_admin_list.items():
        text += "\n🚨 <code>{}</code>".format(admin_group)
        for admin in value:
            text += "\n<code> • </code>{}".format(admin)
        text += "\n"

    text += "\n🤖 Bots:"
    for each_bot in bot_admin_list:
        text += "\n<code> • </code>{}".format(each_bot)

    try:
        msg.edit_text(text, parse_mode=ParseMode.HTML)
    except BadRequest:  # if original message is deleted
        return


__help__ = """
 • `/admins`*:* lista de administradores en el chat

*Solo Administradores:*
 • `/pin`*:* fija silenciosamente el mensaje al que respondió - agregar `'loud'` or`'notify'` Dar notificaciones a los usuarios.
 • `/unpin`*:* elimina el mensaje anclado actualmente
 • `/invitelink`*:* obtiene el enlace de invitaciónk
 • `/link`*:* Lo mismo que invitelink
 • `/promote`*:* Promueve al usuario respondido
 • `/demote`*:* Degrada al usuario respondido
 • `/title <título aquí>`*:*establece un título personalizado para un administrador promovido por el bot
 • `/admincache`*:* forzar la actualización de la lista de administradores
 • `/setgtitle` `<nuevo título>`*:* Establece un nuevo título de chat en su grupo.
 • `/setgpic`*:* Como respuesta a un archivo o foto para configurar una foto de perfil de grupo!
 • `/delgpic`*:* Igual que el anterior pero para eliminar la foto del perfil del grupo.
 • `/setsticker`*:* Como respuesta a alguna pegatina para configurarla como conjunto de pegatinas de grupo!
 • `/setdescription` `<description>`*:* Establece una nueva descripción de chat en el grupo.
 • `/zombies`*:* Escanear cuentas eliminadas
 • `/zombies clean` *:* Limpia cuentas eliminadas
"""

ADMINLIST_HANDLER = DisableAbleCommandHandler("admins", adminlist, run_async=True)
PIN_HANDLER = CommandHandler("pin", pin, filters=Filters.chat_type.groups, run_async=True)
UNPIN_HANDLER = CommandHandler("unpin", unpin, filters=Filters.chat_type.groups, run_async=True)
INVITE_HANDLER = DisableAbleCommandHandler(["invitelink", "link"], invite, run_async=True)
PROMOTE_HANDLER = DisableAbleCommandHandler("promote", promote, run_async=True)
DEMOTE_HANDLER = DisableAbleCommandHandler("demote", demote, run_async=True)
SET_TITLE_HANDLER = CommandHandler("title", set_title, run_async=True)
ADMIN_REFRESH_HANDLER = CommandHandler("admincache", refresh_admin, filters=Filters.chat_type.groups)
CHAT_PIC_HANDLER = CommandHandler("setgpic", setchatpic, filters=Filters.group, run_async=True)
DEL_CHAT_PIC_HANDLER = CommandHandler("delgpic", rmchatpic, filters=Filters.group, run_async=True)
SETCHAT_TITLE_HANDLER = CommandHandler("setgtitle", setchat_title, filters=Filters.group, run_async=True)
SETSTICKET_HANDLER = CommandHandler("setsticker", set_sticker, filters=Filters.group, run_async=True)
SETDESC_HANDLER = CommandHandler("setdescription", set_desc, filters=Filters.group, run_async=True)
    
dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)
dispatcher.add_handler(ADMIN_REFRESH_HANDLER)
dispatcher.add_handler(CHAT_PIC_HANDLER)
dispatcher.add_handler(DEL_CHAT_PIC_HANDLER)
dispatcher.add_handler(SETCHAT_TITLE_HANDLER)
dispatcher.add_handler(SETSTICKET_HANDLER)
dispatcher.add_handler(SETDESC_HANDLER)

__mod_name__ = "Administrador"
__command_list__ = [
    "adminlist",
    "admins",
    "invitelink",
    "promote",
    "demote",
    "admincache",
]
__handlers__ = [
    ADMINLIST_HANDLER,
    PIN_HANDLER,
    UNPIN_HANDLER,
    INVITE_HANDLER,
    PROMOTE_HANDLER,
    DEMOTE_HANDLER,
    SET_TITLE_HANDLER,
    ADMIN_REFRESH_HANDLER,
]
