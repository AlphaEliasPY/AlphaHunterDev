import time
import re

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, Update, Bot
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext, run_async

import HunterAlpha.modules.sql.connection_sql as sql
from HunterAlpha import dispatcher, SUDO_USERS, DEV_USERS
from HunterAlpha.modules.helper_funcs import chat_status
from HunterAlpha.modules.helper_funcs.alternate import send_message, typing_action

user_admin = chat_status.user_admin


@user_admin
@typing_action
def allow_connections(update: Update, context: CallbackContext) -> str:

    chat = update.effective_chat
    args = context.args

    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0]
            if var == "no":
                sql.set_allow_connect_to_chat(chat.id, False)
                send_message(
                    update.effective_message,
                    "Se ha inhabilitado la conexión para este chat",
                )
            elif var == "yes":
                sql.set_allow_connect_to_chat(chat.id, True)
                send_message(
                    update.effective_message,
                    "Se ha habilitado la conexión para este chat",
                )
            else:
                send_message(
                    update.effective_message,
                    "Por favor escribe `yes` o `no`!",
                    parse_mode=ParseMode.MARKDOWN,
                )
        else:
            get_settings = sql.allow_connect_to_chat(chat.id)
            if get_settings:
                send_message(
                    update.effective_message,
                    "Las conexiones a este grupo son *permitidas* para los administradores!",
                    parse_mode=ParseMode.MARKDOWN,
                )
            else:
                send_message(
                    update.effective_message,
                    "La conexión a este grupo es *No permitida* para administradores!",
                    parse_mode=ParseMode.MARKDOWN,
                )
    else:
        send_message(
            update.effective_message, "Este comando es solo para grupos. No en PM!"
        )


@typing_action
def connection_chat(update: Update, context: CallbackContext):

    chat = update.effective_chat
    user = update.effective_user

    conn = connected(context.bot, update, chat, user.id, need_admin=True)

    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type != "private":
            return
        chat = update.effective_chat
        chat_name = update.effective_message.chat.title

    if conn:
        message = "Actualmente estás conectado a {}.\n".format(chat_name)
    else:
        message = "Actualmente no estás conectado en ningún grupo.\n"
    send_message(update.effective_message, message, parse_mode="markdown")


@typing_action
def connect_chat(update: Update, context: CallbackContext):

    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if update.effective_chat.type == "private":
        if args and len(args) >= 1:
            try:
                connect_chat = int(args[0])
                getstatusadmin = context.bot.get_chat_member(
                    connect_chat, update.effective_message.from_user.id
                )
            except ValueError:
                try:
                    connect_chat = str(args[0])
                    get_chat = context.bot.getChat(connect_chat)
                    connect_chat = get_chat.id
                    getstatusadmin = context.bot.get_chat_member(
                        connect_chat, update.effective_message.from_user.id
                    )
                except BadRequest:
                    send_message(update.effective_message, "ID de chat no válido!")
                    return
            except BadRequest:
                send_message(update.effective_message, "ID de chat no válido!")
                return

            isadmin = getstatusadmin.status in ("administrator", "creator")
            isallow = sql.allow_connect_to_chat(connect_chat)

            if (isadmin and isallow) or (user.id in SUDO_USERS):
                connection_status = sql.connect(
                    update.effective_message.from_user.id, connect_chat
                )
                if connection_status:
                    conn_chat = dispatcher.bot.getChat(
                        connected(context.bot, update, chat, user.id, need_admin=True)
                    )
                    chat_name = conn_chat.title
                    send_message(
                        update.effective_message,
                        "Conectado con éxito a *{}*. \nUse /help conexion para comprobar los comandos disponibles.".format(
                            chat_name
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
                else:
                    send_message(update.effective_message, "La conexión falló!")
            else:
                send_message(
                    update.effective_message, "No tienes permiso para conectarte a este chat.!"
                )
        else:
            gethistory = sql.get_history_conn(user.id)
            if gethistory:
                buttons = [
                    InlineKeyboardButton(
                        text="❎ Cerrar", callback_data="connect_close"
                    ),
                    InlineKeyboardButton(
                        text="🧹 Limpiar historial", callback_data="connect_clear"
                    ),
                ]
            else:
                buttons = []
            conn = connected(context.bot, update, chat, user.id, need_admin=True)
            if conn:
                connectedchat = dispatcher.bot.getChat(conn)
                text = "Actualmente estás conectado a *{}* (`{}`)".format(
                    connectedchat.title, conn
                )
                buttons.append(
                    InlineKeyboardButton(
                        text="🔌 Desconectar", callback_data="connect_disconnect"
                    )
                )
            else:
                text = "Escriba el ID de chat o la etiqueta para conectarse!"
            if gethistory:
                text += "\n\n*Historial de conexiones:*\n"
                text += "╒═══「 *Informacion* 」\n"
                text += "│  Ordenados: `El mas nuevo`\n"
                text += "│\n"
                buttons = [buttons]
                for x in sorted(gethistory.keys(), reverse=True):
                    htime = time.strftime("%d/%m/%Y", time.localtime(x))
                    text += "╞═「 *{}* 」\n│   `{}`\n│   `{}`\n".format(
                        gethistory[x]["chat_name"], gethistory[x]["chat_id"], htime
                    )
                    text += "│\n"
                    buttons.append(
                        [
                            InlineKeyboardButton(
                                text=gethistory[x]["chat_name"],
                                callback_data="connect({})".format(
                                    gethistory[x]["chat_id"]
                                ),
                            )
                        ]
                    )
                text += "╘══「 Total {} Chats 」".format(
                    str(len(gethistory)) + " (max)"
                    if len(gethistory) == 5
                    else str(len(gethistory))
                )
                conn_hist = InlineKeyboardMarkup(buttons)
            elif buttons:
                conn_hist = InlineKeyboardMarkup([buttons])
            else:
                conn_hist = None
            send_message(
                update.effective_message,
                text,
                parse_mode="markdown",
                reply_markup=conn_hist,
            )

    else:
        getstatusadmin = context.bot.get_chat_member(
            chat.id, update.effective_message.from_user.id
        )
        isadmin = getstatusadmin.status in ("administrator", "creator")
        isallow = sql.allow_connect_to_chat(chat.id)
        if (isadmin and isallow) or (user.id in SUDO_USERS):
            connection_status = sql.connect(
                update.effective_message.from_user.id, chat.id
            )
            if connection_status:
                chat_name = dispatcher.bot.getChat(chat.id).title
                send_message(
                    update.effective_message,
                    "Conectado con éxito a *{}*.".format(chat_name),
                    parse_mode=ParseMode.MARKDOWN,
                )
                try:
                    sql.add_history_conn(user.id, str(chat.id), chat_name)
                    context.bot.send_message(
                        update.effective_message.from_user.id,
                        "Estas conectado a *{}*. \n[Lista de Ayuda](https://telegra.ph/%F0%9D%94%BC%F0%9D%95%9D-%F0%9D%94%B9%F0%9D%95%A3%F0%9D%95%A0%F0%9D%95%9E%F0%9D%95%92%F0%9D%95%A4-08-04-2) .".format(
                            chat_name
                        ),
                        parse_mode="markdown",
                    )
                except BadRequest:
                    pass
                except Unauthorized:
                    pass
            else:
                send_message(update.effective_message, "La conexión falló!")
        else:
            send_message(
                update.effective_message, "No tienes permiso para conectarte a este chat.!"
            )


def disconnect_chat(update: Update, context: CallbackContext):

    if update.effective_chat.type == "private":
        disconnection_status = sql.disconnect(update.effective_message.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = send_message(
                update.effective_message, "Desconectado del chat!"
            )
        else:
            send_message(update.effective_message, "No estas conectado!")
    else:
        send_message(update.effective_message, "Este comando solo está disponible en PM.")


def connected(bot: Bot, update: Update, chat, user_id, need_admin=True):
    user = update.effective_user

    if chat.type == chat.PRIVATE and sql.get_connected_chat(user_id):

        conn_id = sql.get_connected_chat(user_id).chat_id
        getstatusadmin = bot.get_chat_member(
            conn_id, update.effective_message.from_user.id
        )
        isadmin = getstatusadmin.status in ("administrator", "creator")
        isallow = sql.allow_connect_to_chat(conn_id)

        if (
            (isadmin and isallow)
            or (user.id in SUDO_USERS)
            or (user.id in DEV_USERS)
        ):
            if need_admin is True:
                if (
                    getstatusadmin.status in ("administrator", "creator")
                    or user_id in SUDO_USERS
                    or user.id in DEV_USERS
                ):
                    return conn_id
                else:
                    send_message(
                        update.effective_message,
                        "Debes ser administrador en el grupo conectado!",
                    )
            else:
                return conn_id
        else:
            send_message(
                update.effective_message,
                "El grupo cambió los derechos de conexión o ya no eres administrador.\nTe he desconectado.",
            )
            disconnect_chat(update, bot)
    else:
        return False


CONN_HELP = """
 Las acciones están disponibles con grupos conectados:
  • Ver y editar notas.
  • Ver y editar filtros.
  • Obtener enlace de invitación de chat.
  • Establecer y controlar la configuración de Anti-Inundación.
  • Establecer y controlar la configuración de la lista negra.
  • Establecer bloqueos y desbloqueos en el chat.
  • Activar y desactivar comandos en el chat.
  • Exportación e importación de respaldo de chat.
  • ¡Más en el futuro!"""


def help_connect_chat(update: Update, context: CallbackContext):

    args = context.args

    if update.effective_message.chat.type != "private":
        send_message(update.effective_message, "PM me con ese comando para obtener ayuda.")
        return
    else:
        send_message(update.effective_message, CONN_HELP, parse_mode="markdown")


def connect_button(update: Update, context: CallbackContext):

    query = update.callback_query
    chat = update.effective_chat
    user = update.effective_user

    connect_match = re.match(r"connect\((.+?)\)", query.data)
    disconnect_match = query.data == "connect_disconnect"
    clear_match = query.data == "connect_clear"
    connect_close = query.data == "connect_close"

    if connect_match:
        target_chat = connect_match.group(1)
        getstatusadmin = context.bot.get_chat_member(target_chat, query.from_user.id)
        isadmin = getstatusadmin.status in ("administrator", "creator")
        isallow = sql.allow_connect_to_chat(target_chat)

        if (isadmin and isallow) or (user.id in SUDO_USERS):
            connection_status = sql.connect(query.from_user.id, target_chat)

            if connection_status:
                conn_chat = dispatcher.bot.getChat(
                    connected(context.bot, update, chat, user.id, need_admin=True)
                )
                chat_name = conn_chat.title
                query.message.edit_text(
                    "Conectado con éxito a *{}*. \nUse `/help conexion` para comprobar los comandos disponibles.".format(
                        chat_name
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
                sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
            else:
                query.message.edit_text("Connection failed!")
        else:
            context.bot.answer_callback_query(
                query.id, "No tienes permiso para conectarte a este chat.!", show_alert=True
            )
    elif disconnect_match:
        disconnection_status = sql.disconnect(query.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = query.message.edit_text("Desconectado del chat!")
        else:
            context.bot.answer_callback_query(
                query.id, "No estas conectado!", show_alert=True
            )
    elif clear_match:
        sql.clear_history_conn(query.from_user.id)
        query.message.edit_text("Se borró el historial conectado!")
    elif connect_close:
        query.message.edit_text("Closed.\nPara abrir de nuevo, escriba /connect")
    else:
        connect_chat(update, context)


__mod_name__ = "Conexion"

__help__ = """
A veces, solo desea agregar algunas notas y filtros a un chat grupal, pero no desea que todos lo vean; Aquí es donde entran las conexiones ...
¡Esto le permite conectarse a la base de datos de un chat y agregar cosas sin que los comandos aparezcan en el chat! Por razones obvias, debe ser administrador para agregar cosas; pero cualquier miembro del grupo puede ver tus datos.

 • `/connect`: Se conecta al chat (se puede hacer en grupo `/connect` o `/connect <chat id>` en PM)
 • `/connection`: Lista de chats conectados
 • `/disconnect`: Desconectarse de un chat
 • `/helpconnect`: Enumere los comandos disponibles que se pueden usar de forma remota

*Solo Administradores:*
 • `/allowconnect <yes/no>`: permitir que un usuario se conecte a un chat
"""

CONNECT_CHAT_HANDLER = CommandHandler("connect", connect_chat, run_async=True)
CONNECTION_CHAT_HANDLER = CommandHandler("connection", connection_chat, run_async=True)
DISCONNECT_CHAT_HANDLER = CommandHandler("disconnect", disconnect_chat, run_async=True)
ALLOW_CONNECTIONS_HANDLER = CommandHandler(
    "allowconnect", allow_connections, run_async=True
)
HELP_CONNECT_CHAT_HANDLER = CommandHandler("helpconnect", help_connect_chat)
CONNECT_BTN_HANDLER = CallbackQueryHandler(connect_button, pattern=r"connect", run_async=True)

dispatcher.add_handler(CONNECT_CHAT_HANDLER)
dispatcher.add_handler(CONNECTION_CHAT_HANDLER)
dispatcher.add_handler(DISCONNECT_CHAT_HANDLER)
dispatcher.add_handler(ALLOW_CONNECTIONS_HANDLER)
dispatcher.add_handler(HELP_CONNECT_CHAT_HANDLER)
dispatcher.add_handler(CONNECT_BTN_HANDLER)
