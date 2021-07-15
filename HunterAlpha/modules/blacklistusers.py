# Module to blacklist users and prevent them from using commands by @TheRealPhoenix
import html
import HunterAlpha.modules.sql.blacklistusers_sql as sql
from HunterAlpha import (
    DEV_USERS,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    WHITELIST_USERS,
    dispatcher,
)
from HunterAlpha.modules.helper_funcs.chat_status import dev_plus
from HunterAlpha.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from HunterAlpha.modules.log_channel import gloggable
from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, run_async
from telegram.utils.helpers import mention_html

BLACKLISTWHITELIST = [OWNER_ID] + DEV_USERS + SUDO_USERS + WHITELIST_USERS + SUPPORT_USERS
BLABLEUSERS = [OWNER_ID] + DEV_USERS


@dev_plus
@gloggable
def bl_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Dudo que sea un usuario.")
        return ""

    if user_id == bot.id:
        message.reply_text("¿Cómo se supone que debo hacer mi trabajo si me estoy ignorando?")
        return ""

    if user_id in BLACKLISTWHITELIST:
        message.reply_text("No!\nNotar a los superusuarios es mi trabajo.")
        return ""

    try:
        target_user = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario.")
            return ""
        else:
            raise

    sql.blacklist_user(user_id, reason)
    message.reply_text("Ignoraré la existencia de este usuario.!")
    log_message = (
        f"#BLACKLIST\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(target_user.id, html.escape(target_user.first_name))}"
    )
    if reason:
        log_message += f"\n<b>Razon:</b> {reason}"

    return log_message


@dev_plus
@gloggable
def unbl_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text("Dudo que sea un usuario.")
        return ""

    if user_id == bot.id:
        message.reply_text("Siempre me doy cuenta de mi mismo.")
        return ""

    try:
        target_user = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "Usuario no encontrado":
            message.reply_text("Parece que no puedo encontrar a este usuario.")
            return ""
        else:
            raise

    if sql.is_user_blacklisted(user_id):

        sql.unblacklist_user(user_id)
        message.reply_text("*notifica al usuario*")
        log_message = (
            f"#UNBLACKLIST\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(target_user.id, html.escape(target_user.first_name))}"
        )

        return log_message

    else:
        message.reply_text("Sin embargo, no los estoy ignorando en absoluto.!")
        return ""


@dev_plus
def bl_users(update: Update, context: CallbackContext):
    users = []
    bot = context.bot
    for each_user in sql.BLACKLIST_USERS:
        user = bot.get_chat(each_user)
        reason = sql.get_reason(each_user)

        if reason:
            users.append(
                f"• {mention_html(user.id, html.escape(user.first_name))} :- {reason}"
            )
        else:
            users.append(f"• {mention_html(user.id, html.escape(user.first_name))}")

    message = "<b>Usuarios incluidos en la lista negra</b>\n"
    if not users:
        message += "Nadie está siendo ignorado por el momento."
    else:
        message += "\n".join(users)

    update.effective_message.reply_text(message, parse_mode=ParseMode.HTML)


def __user_info__(user_id):
    is_blacklisted = sql.is_user_blacklisted(user_id)

    text = "En la lista negra: <b>{}</b>"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == dispatcher.bot.id:
        return ""
    if int(user_id) in SUDO_USERS:
        return ""
    if is_blacklisted:
        text = text.format("Yes")
        reason = sql.get_reason(user_id)
        if reason:
            text += f"\nRazon: <code>{reason}</code>"
    else:
        text = text.format("No")

    return text


BL_HANDLER = CommandHandler("ignore", bl_user, run_async=True)
UNBL_HANDLER = CommandHandler("notice", unbl_user, run_async=True)
BLUSERS_HANDLER = CommandHandler("ignoredlist", bl_users, run_async=True)

dispatcher.add_handler(BL_HANDLER)
dispatcher.add_handler(UNBL_HANDLER)
dispatcher.add_handler(BLUSERS_HANDLER)

__mod_name__ = "Usuarios en lista negra"
__handlers__ = [BL_HANDLER, UNBL_HANDLER, BLUSERS_HANDLER]
