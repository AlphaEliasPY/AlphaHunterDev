import html
import json
import os
from typing import Optional

from HunterAlpha import (
    DEV_USERS,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_CHAT,
    SUPPORT_USERS,
    WHITELIST_USERS,
    dispatcher,
)
from HunterAlpha.modules.helper_funcs.chat_status import (
    dev_plus,
    sudo_plus,
    whitelist_plus,
)
from HunterAlpha.modules.helper_funcs.extraction import extract_user
from HunterAlpha.modules.log_channel import gloggable
from telegram import ParseMode, TelegramError, Update
from telegram.ext import CallbackContext, CommandHandler, run_async
from telegram.utils.helpers import mention_html

ELEVATED_USERS_FILE = os.path.join(os.getcwd(), "HunterAlpha/elevated_users.json")


def check_user_id(user_id: int, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    if not user_id:
        reply = "Eso ... ¡es una charla!?"

    elif user_id == bot.id:
        reply = "Esto no funciona de esa manera."

    else:
        reply = None
    return reply


# This can serve as a deeplink example.
# god_mode =
# """ Text here """

# do not async, not a handler
# def send_god_mode(update):
#    update.effective_message.reply_text(
#        god_mode, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

### Deep link example ends


@dev_plus
@gloggable
def addsudo(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in DEV_USERS:
        message.reply_text("¿Eh? el es mas que sudo!")
        return ""

    if user_id in SUDO_USERS:
        message.reply_text("Este usuario ya es sudo")
        return ""

    if user_id in SUPPORT_USERS:
        rt += "Promocionado de usuario de soporte a sudo"
        data["supports"].remove(user_id)
        SUPPORT_USERS.remove(user_id)

    if user_id in WHITELIST_USERS:
        rt += "Promocionado de usuario de la lista blanca a sudo"
        data["whitelists"].remove(user_id)
        WHITELIST_USERS.remove(user_id)

    data["sudos"].append(user_id)
    SUDO_USERS.append(user_id)

    with open(ELEVATED_USERS_FILE, "w") as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + "\nExitosamente promovido a sudo!".format(user_member.first_name)
    )

    log_message = (
        f"#SUDO\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != "private":
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@sudo_plus
@gloggable
def addsupport(
    update: Update,
    context: CallbackContext,
) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in SUDO_USERS:
        rt += "Degradado de sudo para apoyar al usuario"
        data["sudos"].remove(user_id)
        SUDO_USERS.remove(user_id)

    if user_id in SUPPORT_USERS:
        message.reply_text("Este usuario ya es sudo")
        return ""

    if user_id in WHITELIST_USERS:
        rt += "Promocionado de la lista blanca para apoyar al usuario"
        data["whitelists"].remove(user_id)
        WHITELIST_USERS.remove(user_id)

    data["supports"].append(user_id)
    SUPPORT_USERS.append(user_id)

    with open(ELEVATED_USERS_FILE, "w") as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + f"\nPromocionado con éxito {user_member.first_name} Para apoyar al usuario"
    )

    log_message = (
        f"#SUPPORT\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != "private":
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@sudo_plus
@gloggable
def addwhitelist(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)
    rt = ""

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in SUDO_USERS:
        rt += "Degradado de sudo a usuario de la lista blanca"
        data["sudos"].remove(user_id)
        SUDO_USERS.remove(user_id)

    if user_id in SUPPORT_USERS:
        rt += "Degradado de usuario de soporte a usuario de lista blanca"
        data["supports"].remove(user_id)
        SUPPORT_USERS.remove(user_id)

    if user_id in WHITELIST_USERS:
        message.reply_text("Este usuario ya es un usuario de la lista blanca.")
        return ""

    data["whitelists"].append(user_id)
    WHITELIST_USERS.append(user_id)

    with open(ELEVATED_USERS_FILE, "w") as outfile:
        json.dump(data, outfile, indent=4)

    update.effective_message.reply_text(
        rt + f"\nPromocionado con éxito {user_member.first_name} para incluir al usuario en la lista blanca!"
    )

    log_message = (
        f"#WHITELIST\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))} \n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != "private":
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message


@dev_plus
@gloggable
def removesudo(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in DEV_USERS:
        message.reply_text("¿Eh? el es mas que sudo!")
        return ""

    if user_id in SUDO_USERS:
        message.reply_text("Degradado a usuario normal")
        SUDO_USERS.remove(user_id)
        data["sudos"].remove(user_id)

        with open(ELEVATED_USERS_FILE, "w") as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNSUDO\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != "private":
            log_message = "<b>{}:</b>\n".format(html.escape(chat.title)) + log_message

        return log_message

    else:
        message.reply_text("Este usuario no es sudo")
        return ""


@sudo_plus
@gloggable
def removesupport(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in SUPPORT_USERS:
        message.reply_text("Degradado a usuario normal")
        SUPPORT_USERS.remove(user_id)
        data["supports"].remove(user_id)

        with open(ELEVATED_USERS_FILE, "w") as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNSUPPORT\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != "private":
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message

    else:
        message.reply_text("Este usuario no es un usuario de soporte.")
        return ""


@sudo_plus
@gloggable
def removewhitelist(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)
    user_member = bot.getChat(user_id)

    reply = check_user_id(user_id, bot)
    if reply:
        message.reply_text(reply)
        return ""

    with open(ELEVATED_USERS_FILE, "r") as infile:
        data = json.load(infile)

    if user_id in WHITELIST_USERS:
        message.reply_text("Degradación al usuario normal")
        WHITELIST_USERS.remove(user_id)
        data["whitelists"].remove(user_id)

        with open(ELEVATED_USERS_FILE, "w") as outfile:
            json.dump(data, outfile, indent=4)

        log_message = (
            f"#UNWHITELIST\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != "private":
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        message.reply_text("Este usuario no es un usuario de la lista blanca.")
        return ""


@whitelist_plus
def whitelistlist(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    msg = "<b>Usuarios de la lista blanca:</b>\n"
    for each_user in WHITELIST_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)

            msg += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    message.reply_text(msg, parse_mode=ParseMode.HTML)


@whitelist_plus
def supportlist(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    msg = "<b>Usuarios de soporte:</b>\n"
    for each_user in SUPPORT_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            msg += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    message.reply_text(msg, parse_mode=ParseMode.HTML)


@whitelist_plus
def sudolist(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    true_sudo = list(set(SUDO_USERS) - set(DEV_USERS))
    msg = "<b>Usuarios de sudo:</b>\n"
    for each_user in true_sudo:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            msg += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    message.reply_text(msg, parse_mode=ParseMode.HTML)


@whitelist_plus
def devlist(update: Update, context: CallbackContext):
    bot = context.bot
    message = update.effective_message
    true_dev = list(set(DEV_USERS) - {OWNER_ID})
    msg = "<b>Usuarios desarrolladores:</b>\n"
    for each_user in true_dev:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            msg += f"• {mention_html(user_id, html.escape(user.first_name))}\n"
        except TelegramError:
            pass
    message.reply_text(msg, parse_mode=ParseMode.HTML)


__help__ = f"""
*⚠️ Noticia:*
Los comandos enumerados aquí solo funcionan para usuarios con acceso especial y se utilizan principalmente para solucionar problemas y depurar.
Los administradores de grupo / propietarios de grupo no necesitan estos comandos. 

*Lista de todos los usuarios especiales:*
• `/sudolist`: enumera todos los usuarios que tienen acceso sudo al bot
• `/supportlist`: enumera todos los usuarios que están autorizados a utilizar gban, pero que también pueden ser baneados
• `/whitelistlist`: enumera todos los usuarios que no se pueden prohibir, silenciar la inundación o expulsar, pero que los administradores pueden prohibir manualmente
• `/devlist`: enumera todos los usuarios desarrolladores que tendrán los mismos permisos que el propietario
• `/addsudo`: Agrega un usuario como sudo
• `/addsupport`: Agrega un usuario como soporte
• `/addwhitelist`: Agrega un usuario como lista blanca
• `/removesudo`: eliminar un usuario de sudo
• `/removesupport`: eliminar usuario de soporte
• `/removewhitelist`: Eliminar un usuario de la lista blanca

*Transmisión: (solo propietario del bot)*
• *Nota:* esto es compatible con la rebaja básica
• `/broadcastall`: retransmisiones por todas partes
• `/broadcastusers`: Emite también a todos los usuarios.
• `/broadcastgroups`: también transmite todos los grupos

*Información de grupos:*
• `/groups`: enumere los grupos con nombre, ID, los miembros cuentan como un txt
• `/chatlist`: lo mismo que los grupos
• `/leave <ID>`: dejar el grupo, la identificación debe tener un guión
• `/stats`: muestra las estadísticas generales del bot
• `/getchats`: obtiene una lista de nombres de grupos en los que se ha visto al usuario. Solo propietario del bot
• `/ginfo username/link/ID`: extrae el panel de información para todo el grupo

*Control de acceso:* 
• `/ignore`: Lista negra de un usuario para usar el bot por completo
• `/notice`: Elimina al usuario de la lista negra
• `/ignoredlist`: listas de usuarios ignorados

*Herramientas del sistema:* 
• `/ip`: obtiene la ip de la conexión del bot (solo el propietario del bot)
• `/ping`: obtiene el tiempo de ping del bot al servidor de telegramas
• `/speedtest`: ejecuta una prueba de velocidad y le ofrece 2 opciones para elegir, salida de texto o imagen
• `/status`: obtiene información del sistema

*Global Bans:*
• `/gban <id> <razon>`: Gbans el usuario, funciona por respuesta también
• `/ungban`: Desbloquea al usuario, el mismo uso que gban
• `/gbanlist`: genera una lista de usuarios gbanned

*Carga del módulo:*
• `/listmodules`: imprime módulos y sus nombres
• `/unload <nombre>`: descarga el módulo dinámicamente
• `/load <nombre>`: módulo de cargas

*Comandos remotos:*
• `/rban user group`: prohibición remota
• `/runban user group`: des-prohibición remota
• `/rpunch user group`: golpe remoto
• `/rmute user group`: Mudo remoto
• `/runmute user group`: des-silencio remoto
• `/ginfo username/link/ID`: extrae el panel de información para todo el grupo
 
*Depuración y Shell:* 
• `/debug <on/off>`: registra los comandos en updates.txt
• `/logs`: ejecute esto en el grupo de apoyo para obtener registros en pm
• `/eval`: Auto explicativo
• `/sh`: ejecuta el comando de shell (solo propietario del bot)
• `/py`: ejecuta código Python (solo propietario del bot)
• `/clearlocals`: como dice el nombre
• `/dbcleanup`: eliminar cuentas y grupos eliminados de la base de datos

Visite @{SUPPORT_CHAT} para obtener más información.
"""

SUDO_HANDLER = CommandHandler(("addsudo"), addsudo, run_async=True)
SUPPORT_HANDLER = CommandHandler(("addsupport"), addsupport, run_async=True)
WHITELIST_HANDLER = CommandHandler(("addwhitelist"), addwhitelist, run_async=True)
UNSUDO_HANDLER = CommandHandler(("removesudo"), removesudo, run_async=True)
UNSUPPORT_HANDLER = CommandHandler(("removesupport"), removesupport, run_async=True)
UNWHITELIST_HANDLER = CommandHandler(("removewhitelist"), removewhitelist, run_async=True)

WHITELISTLIST_HANDLER = CommandHandler(("whitelistlist"), whitelistlist, run_async=True)
SUPPORTLIST_HANDLER = CommandHandler(("supportlist"), supportlist, run_async=True)
SUDOLIST_HANDLER = CommandHandler(("sudolist"), sudolist, run_async=True)
DEVLIST_HANDLER = CommandHandler(("devlist"), devlist, run_async=True)

dispatcher.add_handler(SUDO_HANDLER)
dispatcher.add_handler(SUPPORT_HANDLER)
dispatcher.add_handler(WHITELIST_HANDLER)
dispatcher.add_handler(UNSUDO_HANDLER)
dispatcher.add_handler(UNSUPPORT_HANDLER)
dispatcher.add_handler(UNWHITELIST_HANDLER)

dispatcher.add_handler(WHITELISTLIST_HANDLER)
dispatcher.add_handler(SUPPORTLIST_HANDLER)
dispatcher.add_handler(SUDOLIST_HANDLER)
dispatcher.add_handler(DEVLIST_HANDLER)

__mod_name__ = "Modo Dios"
__handlers__ = [
    SUDO_HANDLER,
    SUPPORT_HANDLER,
    WHITELIST_HANDLER,
    UNSUDO_HANDLER,
    UNSUPPORT_HANDLER,
    UNWHITELIST_HANDLER,
    WHITELISTLIST_HANDLER,
    SUPPORTLIST_HANDLER,
    SUDOLIST_HANDLER,
    DEVLIST_HANDLER,
]
