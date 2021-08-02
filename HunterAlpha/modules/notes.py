import re, ast
from io import BytesIO
import random
from typing import Optional

import HunterAlpha.modules.sql.notes_sql as sql
from HunterAlpha.modules.sql.clear_cmd_sql import get_clearcmd
from HunterAlpha import LOGGER, JOIN_LOGGER, SUPPORT_CHAT, dispatcher, SUDO_USERS
from HunterAlpha.modules.disable import DisableAbleCommandHandler
from HunterAlpha.modules.helper_funcs.handlers import MessageHandlerChecker
from HunterAlpha.modules.helper_funcs.chat_status import user_admin, connection_status
from HunterAlpha.modules.helper_funcs.misc import build_keyboard, revert_buttons, delete
from HunterAlpha.modules.helper_funcs.msg_types import get_note_type
from HunterAlpha.modules.helper_funcs.string_handling import (
    escape_invalid_curly_brackets,
)
from HunterAlpha.modules.private_notes import getprivatenotes
from telegram import (
    MAX_MESSAGE_LENGTH,
    InlineKeyboardMarkup,
    Message,
    ParseMode,
    Update,
    InlineKeyboardButton,
)
from telegram.error import BadRequest
from telegram.utils.helpers import escape_markdown, mention_markdown
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    CallbackQueryHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import run_async

FILE_MATCHER = re.compile(r"^###file_id(!photo)?###:(.*?)(?:\s|$)")
STICKER_MATCHER = re.compile(r"^###sticker(!photo)?###:")
BUTTON_MATCHER = re.compile(r"^###button(!photo)?###:(.*?)(?:\s|$)")
MYFILE_MATCHER = re.compile(r"^###file(!photo)?###:")
MYPHOTO_MATCHER = re.compile(r"^###photo(!photo)?###:")
MYAUDIO_MATCHER = re.compile(r"^###audio(!photo)?###:")
MYVOICE_MATCHER = re.compile(r"^###voice(!photo)?###:")
MYVIDEO_MATCHER = re.compile(r"^###video(!photo)?###:")
MYVIDEONOTE_MATCHER = re.compile(r"^###video_note(!photo)?###:")

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
}


# Do not async
def get(update: Update, context: CallbackContext, notename, show_none=True, no_format=False):
    bot = context.bot
    user = update.effective_user
    chat_id = update.effective_message.chat.id
    note_chat_id = update.effective_chat.id
    note = sql.get_note(note_chat_id, notename)
    message = update.effective_message  # type: Optional[Message]

    if note:
        if MessageHandlerChecker.check_user(update.effective_user.id):
            return
        # If we're replying to a message, reply to that message (unless it's an error)
        if message.reply_to_message:
            reply_id = message.reply_to_message.message_id
        else:
            reply_id = message.message_id
        if note.is_reply:
            if JOIN_LOGGER:
                try:
                    bot.forward_message(
                        chat_id=chat_id, from_chat_id=JOIN_LOGGER, message_id=note.value
                    )
                except BadRequest as excp:
                    if excp.message == "Mensaje para reenviar no encontrado":
                        message.reply_text(
                            "Parece que este mensaje se ha perdido - lo eliminaré "
                            "de tu lista de notas."
                        )
                        sql.rm_note(note_chat_id, notename)
                    else:
                        raise
            else:
                try:
                    bot.forward_message(
                        chat_id=chat_id, from_chat_id=chat_id, message_id=note.value
                    )
                except BadRequest as excp:
                    if excp.message == "Mensaje para reenviar no encontrado":
                        message.reply_text(
                            "Parece que se eliminó el remitente original de esta nota "
                            "su mensaje - lo siento! Haga que el administrador de su bot comience a usar un "
                            "volcado de mensajes para evitar esto. Eliminaré esta nota de "
                            "tus notas guardadas."
                        )
                        sql.rm_note(note_chat_id, notename)
                    else:
                        raise
        else:
            VALID_NOTE_FORMATTERS = [
                "first",
                "last",
                "fullname",
                "username",
                "id",
                "chatname",
                "mention",
            ]
            valid_format = escape_invalid_curly_brackets(
                note.value, VALID_NOTE_FORMATTERS
            )
            if valid_format:
                if not no_format:
                    if "%%%" in valid_format:
                        split = valid_format.split("%%%")
                        if all(split):
                            text = random.choice(split)
                        else:
                            text = valid_format
                    else:
                        text = valid_format
                else:
                    text = valid_format
                text = text.format(
                    first=escape_markdown(message.from_user.first_name),
                    last=escape_markdown(
                        message.from_user.last_name or message.from_user.first_name
                    ),
                    fullname=escape_markdown(
                        " ".join(
                            [message.from_user.first_name, message.from_user.last_name]
                            if message.from_user.last_name
                            else [message.from_user.first_name]
                        )
                    ),
                    username="@" + message.from_user.username
                    if message.from_user.username
                    else mention_markdown(
                        message.from_user.id, message.from_user.first_name
                    ),
                    mention=mention_markdown(
                        message.from_user.id, message.from_user.first_name
                    ),
                    chatname=escape_markdown(
                        message.chat.title
                        if message.chat.type != "private"
                        else message.from_user.first_name
                    ),
                    id=message.from_user.id,
                )
            else:
                text = ""

            keyb = []
            parseMode = ParseMode.MARKDOWN
            buttons = sql.get_buttons(note_chat_id, notename)
            if no_format:
                parseMode = None
                text += revert_buttons(buttons)
            else:
                keyb = build_keyboard(buttons)

            keyboard = InlineKeyboardMarkup(keyb)

            try:
                setting = getprivatenotes(chat_id)
                if note.msgtype in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    if setting:
                        bot.send_message(
                            user.id,
                            text,
                            parse_mode=parseMode,
                            disable_web_page_preview=True,
                            reply_markup=keyboard,
                        )
                    else:
                        delmsg = bot.send_message(
                            chat_id,
                            text,
                            reply_to_message_id=reply_id,
                            parse_mode=parseMode,
                            disable_web_page_preview=True,
                            reply_markup=keyboard,
                        )

                        cleartime = get_clearcmd(chat_id, "notes")

                        if cleartime:
                            context.dispatcher.run_async(delete, delmsg, cleartime.time)

                elif note.msgtype in (sql.Types.STICKER, sql.Types.STICKER):
                    if setting:
                        ENUM_FUNC_MAP[note.msgtype](
                            user.id,
                            note.file,
                            reply_to_message_id=reply_id,
                            reply_markup=keyboard,
                        )
                    else:
                        delmsg = ENUM_FUNC_MAP[note.msgtype](
                            chat_id,
                            note.file,
                            reply_to_message_id=reply_id,
                            reply_markup=keyboard,
                        )

                        cleartime = get_clearcmd(chat_id, "notes")

                        if cleartime:
                            context.dispatcher.run_async(delete, delmsg, cleartime.time)
                else:
                    if setting:
                        ENUM_FUNC_MAP[note.msgtype](
                            user.id,
                            note.file,
                            caption=text,
                            reply_to_message_id=reply_id,
                            parse_mode=parseMode,
                            reply_markup=keyboard,
                        )
                    else:
                        delmsg = ENUM_FUNC_MAP[note.msgtype](
                            chat_id,
                            note.file,
                            caption=text,
                            reply_to_message_id=reply_id,
                            parse_mode=parseMode,
                            reply_markup=keyboard,
                        )

                        cleartime = get_clearcmd(chat_id, "notes")

                        if cleartime:
                            context.dispatcher.run_async(delete, delmsg, cleartime.time)

            except BadRequest as excp:
                if excp.message == "Entity_mention_user_invalid":
                    message.reply_text(
                        "Parece que trataste de mencionar a alguien a quien nunca había visto antes. Si tú realmente "
                        "quiero mencionarlos, reenviarme uno de sus mensajes y podré "
                        "Etiquetarlos!"
                    )
                elif FILE_MATCHER.match(note.value):
                    message.reply_text(
                        "Esta nota era un archivo importado incorrectamente de otro bot - no puedo usar"
                        "eso. Si realmente lo necesita, tendrá que guardarlo nuevamente. En "
                        "mientras tanto, lo eliminaré de tu lista de notas."
                    )
                    sql.rm_note(note_chat_id, notename)
                else:
                    message.reply_text(
                        "Esta nota no se pudo enviar porque tiene un formato incorrecto. Invitar a entrar "
                        f"@{SUPPORT_CHAT} si no puedes averiguar por qué!"
                    )
                    LOGGER.exception(
                        "No se pudo analizar el mensaje #%s en el chat %s",
                        notename,
                        str(note_chat_id),
                    )
                    LOGGER.warning("Message was: %s", str(note.value))
        return
    elif show_none:
        message.reply_text("Esta nota no existe")


@connection_status
def cmd_get(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    if len(args) >= 2 and args[1].lower() == "noformat":
        get(update, context, args[0].lower(), show_none=True, no_format=True)
    elif len(args) >= 1:
        get(update, context, args[0].lower(), show_none=True)
    else:
        update.effective_message.reply_text("Get rekt")


@connection_status
def hash_get(update: Update, context: CallbackContext):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:].lower()
    get(update, context, no_hash, show_none=False)


@connection_status
def slash_get(update: Update, context: CallbackContext):
    message, chat_id = update.effective_message.text, update.effective_chat.id
    no_slash = message[1:]
    note_list = sql.get_all_chat_notes(chat_id)

    try:
        noteid = note_list[int(no_slash) - 1]
        note_name = str(noteid).strip(">").split()[1]
        get(update, context, note_name, show_none=False)
    except IndexError:
        update.effective_message.reply_text("Nota incorrecta ID 😾")


@user_admin
@connection_status
def save(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message  # type: Optional[Message]

    note_name, text, data_type, content, buttons = get_note_type(msg)
    note_name = note_name.lower()
    if data_type is None:
        msg.reply_text("Amigo, no hay nota")
        return

    sql.add_note_to_db(
        chat_id, note_name, text, data_type, buttons=buttons, file=content
    )

    msg.reply_text(
        f"¡Yas! Agregado `{note_name}`.\nConsíguelo con /get `{note_name}`, o `#{note_name}`",
        parse_mode=ParseMode.MARKDOWN,
    )

    if msg.reply_to_message and msg.reply_to_message.from_user.is_bot:
        if text:
            msg.reply_text(
                "Parece que estás intentando guardar un mensaje de un bot. Desafortunadamente, "
                "los bots no pueden reenviar mensajes de bot, por lo que no puedo guardar el mensaje exacto. "
                "\nGuardaré todo el texto que pueda, pero si quieres más, tendrás que "
                "reenvíe el mensaje usted mismo y luego guárdelo."
            )
        else:
            msg.reply_text(
                "Los bots están un poco impedidos por el telegram, lo que dificulta que los bots"
                "interactuar con otros bots, por lo que no puedo guardar este mensaje "
                "como lo haría normalmente - te importaría reenviarlo y "
                "luego guardando ese nuevo mensaje? Gracias!"
            )
        return


@user_admin
@connection_status
def clear(update: Update, context: CallbackContext):
    args = context.args
    chat_id = update.effective_chat.id
    if len(args) >= 1:
        notename = args[0].lower()

        if sql.rm_note(chat_id, notename):
            update.effective_message.reply_text("Nota eliminada con éxito.")
        else:
            update.effective_message.reply_text("Esa no es una nota en mi base de datos!")


def clearall(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        update.effective_message.reply_text(
            "Solo el propietario del chat puede borrar todas las notas a la vez."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Eliminar todas las notas", callback_data="notes_rmall"
                    )
                ],
                [InlineKeyboardButton(text="Cancelar", callback_data="notes_cancel")],
            ]
        )
        update.effective_message.reply_text(
            f"¿Está seguro de que desea borrar TODAS las notas en {chat.title}? Esta acción no se puede deshacer.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


def clearall_btn(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = update.effective_chat
    message = update.effective_message
    member = chat.get_member(query.from_user.id)
    if query.data == "notes_rmall":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            note_list = sql.get_all_chat_notes(chat.id)
            try:
                for notename in note_list:
                    note = notename.name.lower()
                    sql.rm_note(chat.id, note)
                message.edit_text("Borró todas las notas.")
            except BadRequest:
                return

        if member.status == "administrator":
            query.answer("Solo el dueño del chat puede hacer esto..")

        if member.status == "member":
            query.answer("Necesitas ser administrador para hacer esto.")
    elif query.data == "notes_cancel":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            message.edit_text("Se canceló el borrado de todas las notas.")
            return
        if member.status == "administrator":
            query.answer("Solo el dueño del chat puede hacer esto..")
        if member.status == "member":
            query.answer("Necesitas ser administrador para hacer esto.")


@connection_status
def list_notes(update: Update, context: CallbackContext):
    bot = context.bot
    user = update.effective_user
    chat_id = update.effective_chat.id
    note_list = sql.get_all_chat_notes(chat_id)
    notes = len(note_list) + 1
    msg = "Obtener nota por `/número de nota` o `#nombre de nota` \n\n  *ID*    *Nota* \n"
    msg_pm = f"*Notas de {update.effective_chat.title}* \nObtener nota por `/número de nota` o `#nombre de nota` en grupo \n\n  *ID*    *Nota* \n"
    for note_id, note in zip(range(1, notes), note_list):
        if note_id < 10:
            note_name = f"{note_id:2}.  `{(note.name.lower())}`\n"
        else:
            note_name = f"{note_id}.  `{(note.name.lower())}`\n"
        if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
            msg_pm = ""
        msg += note_name
        msg_pm += note_name

    if not note_list:
        try:
            update.effective_message.reply_text("No hay notas en este chat!")
        except BadRequest:
            update.effective_message.reply_text("No hay notas en este chat!", quote=False)

    elif len(msg) != 0:
        setting = getprivatenotes(chat_id)
        if setting == True:
            bot.send_message(user.id, msg_pm, parse_mode=ParseMode.MARKDOWN)
        else:
            delmsg = update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

            cleartime = get_clearcmd(chat_id, "notes")

            if cleartime:
                context.dispatcher.run_async(delete, delmsg, cleartime.time)


def __import_data__(chat_id, data):
    failures = []
    for notename, notedata in data.get("extra", {}).items():
        match = FILE_MATCHER.match(notedata)
        matchsticker = STICKER_MATCHER.match(notedata)
        matchbtn = BUTTON_MATCHER.match(notedata)
        matchfile = MYFILE_MATCHER.match(notedata)
        matchphoto = MYPHOTO_MATCHER.match(notedata)
        matchaudio = MYAUDIO_MATCHER.match(notedata)
        matchvoice = MYVOICE_MATCHER.match(notedata)
        matchvideo = MYVIDEO_MATCHER.match(notedata)
        matchvn = MYVIDEONOTE_MATCHER.match(notedata)

        if match:
            failures.append(notename)
            notedata = notedata[match.end() :].strip()
            if notedata:
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)
        elif matchsticker:
            content = notedata[matchsticker.end() :].strip()
            if content:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.STICKER, file=content
                )
        elif matchbtn:
            parse = notedata[matchbtn.end() :].strip()
            notedata = parse.split("<###button###>")[0]
            buttons = parse.split("<###button###>")[1]
            buttons = ast.literal_eval(buttons)
            if buttons:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.BUTTON_TEXT,
                    buttons=buttons,
                )
        elif matchfile:
            file = notedata[matchfile.end() :].strip()
            file = file.split("<###TYPESPLIT###>")
            notedata = file[1]
            content = file[0]
            if content:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.DOCUMENT, file=content
                )
        elif matchphoto:
            photo = notedata[matchphoto.end() :].strip()
            photo = photo.split("<###TYPESPLIT###>")
            notedata = photo[1]
            content = photo[0]
            if content:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.PHOTO, file=content
                )
        elif matchaudio:
            audio = notedata[matchaudio.end() :].strip()
            audio = audio.split("<###TYPESPLIT###>")
            notedata = audio[1]
            content = audio[0]
            if content:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.AUDIO, file=content
                )
        elif matchvoice:
            voice = notedata[matchvoice.end() :].strip()
            voice = voice.split("<###TYPESPLIT###>")
            notedata = voice[1]
            content = voice[0]
            if content:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.VOICE, file=content
                )
        elif matchvideo:
            video = notedata[matchvideo.end() :].strip()
            video = video.split("<###TYPESPLIT###>")
            notedata = video[1]
            content = video[0]
            if content:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.VIDEO, file=content
                )
        elif matchvn:
            video_note = notedata[matchvn.end() :].strip()
            video_note = video_note.split("<###TYPESPLIT###>")
            notedata = video_note[1]
            content = video_note[0]
            if content:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.VIDEO_NOTE, file=content
                )
        else:
            sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)

    if failures:
        with BytesIO(str.encode("\n".join(failures))) as output:
            output.name = "failed_imports.txt"
            dispatcher.bot.send_document(
                chat_id,
                document=output,
                filename="failed_imports.txt",
                caption="Estos archivos /fotos no se pudieron importar debido a que se originaron "
                "de otro bot. Esta es una restricción de la API de telegram y no puede "
                "ser evitado. Lo siento por los inconvenientes ocasionados!",
            )


def __stats__():
    return f"• {sql.num_notes()} notes, across {sql.num_chats()} chats."


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    notes = sql.get_all_chat_notes(chat_id)
    return f"Existen `{len(notes)}` notas en este chat."


__help__ = """
 • `/get <nombredeNota>`*:* obtiene la nota con este nombre de nota
 • `#<nombre de nota>`*:* igual que / get
 • `/notes` o `/saved`*:* enumerar todas las notas guardadas en este chat
 • `/number` *:* Sacará la nota de ese número en la lista
Si desea recuperar el contenido de una nota sin ningún formato, use `/get <nombrenota> noformat`. Esto puede \
ser útil al actualizar una nota actual

*Solo administradores:*
 • `/save <nombredeNota> <notedatos>`*:* guarda los datos de la nota como una nota con el nombre de la nota
Se puede agregar un botón a una nota utilizando la sintaxis de enlace de rebajas estándar; el enlace debe ir precedido de un \
`buttonurl:` sección, como tal: `[somelink](buttonurl:example.com)`. Cheque [Ayuda](https://telegra.ph/%F0%9D%94%BC%F0%9D%95%9D-%F0%9D%94%B9%F0%9D%95%A3%F0%9D%95%A0%F0%9D%95%9E%F0%9D%95%92%F0%9D%95%A4-08-02-2) para más información.
 • `/save <notename>`*:* guarda el mensaje respondido como una nota con el nombre notename
 Separe las respuestas de diferencias por `%%%` para obtener notas aleatorias
 *Ejemplo:* 
 `/save nombre de nota
 Respuesta 1
 %%%
 Respuesta 2
 %%%
 Respuesta 3`
 • `/clear <nombre>`*:* nota clara con este nombree
 • `/removeallnotes`*:* elimina todas las notas del grupo
 *Nota:* Los nombres de las notas no distinguen entre mayúsculas y minúsculas y se convierten automáticamente a minúsculas antes de guardarse.
 • `/privatenotes <on/yes/1/off/no/0>`: habilitar o deshabilitar notas privadas en el chat
"""

__mod_name__ = "Notas"

GET_HANDLER = CommandHandler("get", cmd_get, run_async=True)
HASH_GET_HANDLER = MessageHandler(Filters.regex(r"^#[^\s]+"), hash_get, run_async=True)
SLASH_GET_HANDLER = MessageHandler(Filters.regex(r"^/\d+$"), slash_get, run_async=True)
SAVE_HANDLER = CommandHandler("save", save, run_async=True)
DELETE_HANDLER = CommandHandler("clear", clear, run_async=True)

LIST_HANDLER = DisableAbleCommandHandler(["notes", "saved"], list_notes, admin_ok=True, run_async=True)

CLEARALL = DisableAbleCommandHandler("removeallnotes", clearall, run_async=True)
CLEARALL_BTN = CallbackQueryHandler(clearall_btn, pattern=r"notes_.*", run_async=True)

dispatcher.add_handler(GET_HANDLER)
dispatcher.add_handler(SAVE_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(HASH_GET_HANDLER)
dispatcher.add_handler(SLASH_GET_HANDLER)
dispatcher.add_handler(CLEARALL)
dispatcher.add_handler(CLEARALL_BTN)
