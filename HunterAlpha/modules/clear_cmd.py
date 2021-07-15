from telegram import Update, Bot, ParseMode
from telegram.ext import CommandHandler, CallbackContext, run_async

import HunterAlpha.modules.sql.clear_cmd_sql as sql
from HunterAlpha import dispatcher
from HunterAlpha.modules.helper_funcs.chat_status import user_admin, connection_status


@user_admin
@connection_status
def clearcmd(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    msg = ""

    commands = [
    "afk",
    "cash",
    "checkfw",
    "covid",
    "filters",
    "fun",
    "getfw",
    "github",
    "imdb",
    "info",
    "lyrics",
    "magisk",
    "miui",
    "notes",    
    "orangefox",
    "phh",
    "ping",
    "purge",
    "reverse",
    "speedtest",
    "time",
    "tr",
    "tts",
    "twrp",
    "ud",
    "wall",
    "weather",
    "welcome",
    "wiki",
    "youtube",
    "zombies",
    ]

    if len(args) == 0:
        commands = sql.get_allclearcmd(chat.id)
        if commands:
            msg += "*Comando - Tiempo*\n"
            for cmd in commands:
                msg += f"`{cmd.cmd} - {cmd.time} secs`\n"  
        else:
            msg = f"No se ha establecido un tiempo de eliminación para ningún comando en *{chat.title}*"

    elif len(args) == 1:
        cmd = args[0].lower()
        if cmd == "list":
            msg = "Los comandos disponibles son:\n"
            for cmd in commands:
                msg += f"• `{cmd}`\n"
        elif cmd == "restore":
            delcmd = sql.del_allclearcmd(chat.id)
            msg = "Se eliminaron todos los comandos de la lista."
        else:
            cmd = sql.get_clearcmd(chat.id, cmd)
            if cmd:
                msg = f"`{cmd.cmd}` la salida está configurada para ser eliminada después *{cmd.time}* segundos en *{chat.title}*"
            else:
                if cmd not in commands:
                    msg = "Comando inválido. Consulte la ayuda del módulo para obtener más detalles"
                else:
                    msg = f"Esta salida de comando no se ha configurado para eliminarse en *{chat.title}*"

    elif len(args) == 2:
        cmd = args[0].lower()
        time = args[1]
        if cmd in commands:
            if time == "restaurar":
                sql.del_clearcmd(chat.id, cmd)
                msg = f"Removido `{cmd}` from list"
            elif (5 <= int(time) <= 300):
                sql.set_clearcmd(chat.id, cmd, time)
                msg = f"`{cmd}` la salida se eliminará después *{time}* segundos en *{chat.title}*"
            else:
               msg = "El tiempo debe estar entre 5 y 300 segundos."
        else:
            msg = "Especifique un comando válido. Utilice `/clearcmd list` para ver los comandos disponibles"
                
    else:
        msg = "No entiendo qué estás tratando de hacer. Consulte la ayuda del módulo para obtener más detalles"

    message.reply_text(
        text = msg,
        parse_mode = ParseMode.MARKDOWN
    )


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = """
*Obtener la configuración del módulo:*
• `/clearcmd`: proporciona todos los comandos que se han configurado en el grupo actual con su tiempo de eliminación
• `/clearcmd list`: enumerar todos los comandos disponibles para este módulo
• `/clearcmd <commando>`: obtener el tiempo de eliminación para un `<comando> específico`

*Establecer la configuración del módulo:*
• `/clearcmd <comando> <tiempo>`: set a deletion `<time>` para un `<comando>` específico en el grupo actual. Todas las salidas de ese comando se eliminarán en ese grupo después del valor de tiempo en segundos. El tiempo se puede configurar entre 5 y 300 segundos.

*Restaurar la configuración del módulo:*
• `/clearcmd restore`: el tiempo de eliminación establecido para TODOS los comandos se eliminará en el grupo actual
• `/clearcmd <comando> restore`: el tiempo de eliminación establecido para un `<comando>` específico se eliminará en el grupo actual
"""

CLEARCMD_HANDLER = CommandHandler("clearcmd", clearcmd, run_async=True)

dispatcher.add_handler(CLEARCMD_HANDLER)

__mod_name__ = "limpiar-CMD"
__command_list__ = ["clearcmd"]
__handlers__ = [CLEARCMD_HANDLER]
