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
        message.reply_text("I doubt that's a user.")
        return log_message
    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise
        message.reply_text("Can't seem to find this person.")
        return log_message
    if user_id == bot.id:
        message.reply_text("Oh yeah, ban myself, noob!")
        return log_message

    if is_user_ban_protected(chat, user_id, member) and user not in DEV_USERS:
        if user_id == OWNER_ID:
            message.reply_text("Trying to put me against God huh?")
        elif user_id in DEV_USERS:
            message.reply_text("I can't act against our own.")
        elif user_id in SUDO_USERS:
            message.reply_text(
                "Fighting this sudo user here will put users lives at risk."
            )
        elif user_id in SUPPORT_USERS:
            message.reply_text("Bring a developer user to fight a support user.")
        elif user_id in WHITELIST_USERS:
            message.reply_text("Whitelist users cannot be banned.")
        else:
            message.reply_text("This user has immunity and cannot be banned.")
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
        log += "\n<b>Reason:</b> {}".format(reason)

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
            reply += f"\n<code> </code><b>•  Reason:</b> \n{html.escape(reason)}"
        bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML,)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            if silent:
                return log
            message.reply_text("Banned!", quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Uhm...that didn't work...")

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
        message.reply_text("I doubt that's a user.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise
        message.reply_text("I can't seem to find this user.")
        return log_message
    if user_id == bot.id:
        message.reply_text("I'm not gonna BAN myself, are you crazy?")
        return log_message

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("I don't feel like it.")
        return log_message

    if not reason:
        message.reply_text("You haven't specified a time to ban this user for!")
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
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.sendMessage(
            chat.id,
            f"Banned! User {mention_html(member.user.id, html.escape(member.user.first_name))} "
            f"will be banned for {time_val}.",
            parse_mode=ParseMode.HTML,
        )
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(
                f"Banned! User will be banned for {time_val}.", quote=False
            )
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            message.reply_text("Well damn, I can't ban that user.")

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
        message.reply_text("I doubt that's a user.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        message.reply_text("I can't seem to find this user.")
        return log_message
    if user_id == bot.id:
        message.reply_text("Yeahhh I'm not gonna do that.")
        return log_message

    if is_user_ban_protected(chat, user_id):
        message.reply_text("I really wish I could punch this user....")
        return log_message

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        reply = (
            f"<code>❕</code><b>Punch Event</b>\n"
            f"<code> </code><b>•  User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
        )
        if reason:
            reply += f"<code> </code><b>•  Reason:</b> {html.escape(reason)}"
        bot.sendMessage(chat.id, reply, parse_mode=ParseMode.HTML
        )
        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#KICKED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            log += f"\n<b>Reason:</b> {reason}"

        return log

    else:
        message.reply_text("Well damn, I can't punch that user.")

    return log_message


@bot_admin
@can_restrict
def punchme(update: Update, context: CallbackContext):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("I wish I could... but you're an admin.")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("Punches you out of the group")
    else:
        update.effective_message.reply_text("Huh? I can't :/")


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
        message.reply_text("I doubt that's a user.")
        return log_message

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise
        message.reply_text("I can't seem to find this user.")
        return log_message
    if user_id == bot.id:
        message.reply_text("How would I unban myself if I wasn't here...?")
        return log_message

    if is_user_in_chat(chat, user_id):
        message.reply_text("Isn't this person already here??")
        return log_message

    chat.unban_member(user_id)
    message.reply_text("Yep, this user can join!")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )
    if reason:
        log += f"\n<b>Reason:</b> {reason}"

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
        message.reply_text("Give a valid chat ID.")
        return

    chat = bot.getChat(chat_id)

    try:
        member = chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user.")
            return
        else:
            raise

    if is_user_in_chat(chat, user.id):
        message.reply_text("Aren't you already in the chat??")
        return

    chat.unban_member(user.id)
    message.reply_text("Yep, I have unbanned you.")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
    )

    return log


__help__ = """
 • `/punchme`*:* punchs the user who issued the command
 • `/kickme`*:* same as punchme

*Admins only:*
 • `/ban <userhandle>`*:* bans a user. (via handle, or reply)
 • `/sban <userhandle>`*:* Silently ban a user. Deletes command, Replied message and doesn't reply. (via handle, or reply)
 • `/tban <userhandle> x(m/h/d)`*:* bans a user for `x` time. (via handle, or reply). `m` = `minutes`, `h` = `hours`, `d` = `days`.
 • `/unban <userhandle>`*:* unbans a user. (via handle, or reply)
 • `/punch <userhandle> <reason>(optional)`*:* Punches a user out of the group, (via handle, or reply)
 • `/kick <userhandle>`*:* same as punch
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

__mod_name__ = "Bans"
__handlers__ = [
    BAN_HANDLER,
    TEMPBAN_HANDLER,
    PUNCH_HANDLER,
    UNBAN_HANDLER,
    ROAR_HANDLER,
    PUNCHME_HANDLER,
]
