import html
from HunterAlpha.modules.disable import DisableAbleCommandHandler
from HunterAlpha import dispatcher, SUDO_USERS
from HunterAlpha.modules.helper_funcs.extraction import extract_user
from telegram.ext import CallbackContext, run_async, CallbackQueryHandler
import HunterAlpha.modules.sql.approve_sql as sql
from HunterAlpha.modules.helper_funcs.chat_status import user_admin
from HunterAlpha.modules.log_channel import loggable
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.utils.helpers import mention_html
from telegram.error import BadRequest


@loggable
@user_admin
def approve(update: Update, context: CallbackContext):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "No sé de quién estás hablando, necesitarás especificar un usuario!"
        )
        return ""
    try:
        member = chat.get_member(user_id)
    except BadRequest:
        return ""
    if member.status == "administrator" or member.status == "creator":
        message.reply_text(
            "El usuario ya es administrador: los bloqueos, las listas de bloqueo y la protección contra Anti-inundaciones ya no se aplican a ellos."
        )
        return ""
    if sql.is_approved(message.chat_id, user_id):
        message.reply_text(
            f"[{member.user['first_name']}](tg://user?id={member.user['id']}) ya está aprobado en {chat_title}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ""
    sql.approve(message.chat_id, user_id)
    message.reply_text(
        f"[{member.user['first_name']}](tg://user?id={member.user['id']}) ha sido aprobado en {chat_title}! Ahora serán ignorados por acciones de administración automatizadas como bloqueos, listas de bloqueo y anti-inundación..",
        parse_mode=ParseMode.MARKDOWN,
    )
    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#APPROVED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    return log_message


@loggable
@user_admin
def disapprove(update: Update, context: CallbackContext):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(
            "No sé de quién estás hablando, necesitarás especificar un usuario!"
        )
        return ""
    try:
        member = chat.get_member(user_id)
    except BadRequest:
        return ""
    if member.status == "administrator" or member.status == "creator":
        message.reply_text("Este usuario es un administrador, no puede ser desaprobado..")
        return ""
    if not sql.is_approved(message.chat_id, user_id):
        message.reply_text(f"{member.user['first_name']} aún no está aprobado!")
        return ""
    sql.disapprove(message.chat_id, user_id)
    message.reply_text(
        f"{member.user['first_name']} Ya no está aprobado en {chat_title}."
    )
    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNAPPROVED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    return log_message


@user_admin
def approved(update: Update, context: CallbackContext):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    msg = "Los siguientes usuarios están aprobados.\n"
    approved_users = sql.list_approved(message.chat_id)
    for i in approved_users:
        member = chat.get_member(int(i.user_id))
        msg += f"- `{i.user_id}`: {member.user['first_name']}\n"
    if msg.endswith("aprobado.\n"):
        message.reply_text(f"No hay usuarios aprobados en {chat_title}.")
        return ""
    else:
        message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


@user_admin
def approval(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user_id = extract_user(message, args)
    member = chat.get_member(int(user_id))
    if not user_id:
        message.reply_text(
            "No sé de quién estás hablando, necesitarás especificar un usuario!"
        )
        return ""
    if sql.is_approved(message.chat_id, user_id):
        message.reply_text(
            f"{member.user['first_name']} es un usuario aprobado. Los bloqueos, anti-inundación y listas de bloqueo no se aplicarán a ellos."
        )
    else:
        message.reply_text(
            f"{member.user['first_name']} no es un usuario aprobado. Se ven afectados por los comandos normales.."
        )


def unapproveall(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        update.effective_message.reply_text(
            "Solo el propietario del chat puede desaprobar a todos los usuarios a la vez."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Desaprobar a todos los usuarios", callback_data="unapproveall_user"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Cancelar", callback_data="unapproveall_cancel"
                    )
                ],
            ]
        )
        update.effective_message.reply_text(
            f"Está seguro de que desea desaprobar a TODOS los usuarios en {chat.title}? su acción no se puede deshacer.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


def unapproveall_btn(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = update.effective_chat
    message = update.effective_message
    member = chat.get_member(query.from_user.id)
    if query.data == "unapproveall_user":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            approved_users = sql.list_approved(chat.id)
            users = [int(i.user_id) for i in approved_users]
            for user_id in users:
                sql.disapprove(chat.id, user_id)      
            message.edit_text("Todos los usuarios de este chat no aprobados con éxito.")
            return

        if member.status == "administrator":
            query.answer("Solo el dueño del chat puede hacer esto..")

        if member.status == "member":
            query.answer("Necesitas ser administrador para hacer esto.")
    elif query.data == "unapproveall_cancel":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            message.edit_text("La eliminación de todos los usuarios aprobados ha sido cancelada.")
            return ""
        if member.status == "administrator":
            query.answer("Solo el dueño del chat puede hacer esto..")
        if member.status == "member":
            query.answer("Necesitas ser administrador para hacer esto.")


__help__ = """
A veces, puede confiar en que un usuario no enviará contenido no deseado.
Tal vez no sea suficiente para convertirlos en administradores, pero es posible que no se apliquen bloqueos, listas negras y antiflood a ellos.

Para eso están las aprobaciones: aprobar a usuarios confiables para permitirles enviar 

*Comandos De Administrador:*
- `/approval`*:* Verifique el estado de aprobación de un usuario en este chat.
- `/approve`*:* Aprobación de un usuario. Las cerraduras, las listas negras y el anti-inundación ya no se les aplicarán.
- `/unapprove`*:* No aprobar a un usuario. Ahora estarán sujetos a bloqueos, listas negras y antiinundación nuevamente..
- `/approved`*:* Lista de todos los usuarios aprobados.
- `/unapproveall`*:*vDesaprobar *TODOS* los usuarios en un chat. Esto no se puede deshacer.
"""

APPROVE = DisableAbleCommandHandler("approve", approve, run_async=True)
DISAPPROVE = DisableAbleCommandHandler("unapprove", disapprove, run_async=True)
APPROVED = DisableAbleCommandHandler("approved", approved, run_async=True)
APPROVAL = DisableAbleCommandHandler("approval", approval, run_async=True)
UNAPPROVEALL = DisableAbleCommandHandler("unapproveall", unapproveall, run_async=True)
UNAPPROVEALL_BTN = CallbackQueryHandler(unapproveall_btn, pattern=r"unapproveall_.*", run_async=True)

dispatcher.add_handler(APPROVE)
dispatcher.add_handler(DISAPPROVE)
dispatcher.add_handler(APPROVED)
dispatcher.add_handler(APPROVAL)
dispatcher.add_handler(UNAPPROVEALL)
dispatcher.add_handler(UNAPPROVEALL_BTN)

__mod_name__ = "Aprobacion"
__command_list__ = ["approve", "unapprove", "approved", "approval"]
__handlers__ = [APPROVE, DISAPPROVE, APPROVED, APPROVAL]
