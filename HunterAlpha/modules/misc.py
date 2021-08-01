from HunterAlpha.modules.helper_funcs.chat_status import sudo_plus
from HunterAlpha.modules.disable import DisableAbleCommandHandler
from HunterAlpha import dispatcher

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ParseMode, Update
from telegram.ext.dispatcher import run_async
from telegram.ext import CallbackContext, Filters, CommandHandler

MARKDOWN_HELP = f"""
Markdown es una herramienta de formato muy poderosa compatible con telegram. {dispatcher.bot.first_name} tiene algunas mejoras, para asegurarse de que \
los mensajes guardados se analizan correctamente y le permiten crear botones.

• <code> _italic_ </code>: ajustar el texto con '_' producirá texto en cursiva
• <code> * bold * </code>: ajustar el texto con '*' producirá texto en negrita
• <code> `code` </code>: ajustar el texto con '`' producirá texto monoespaciado, también conocido como 'código'
• <code> [sometext] (someURL) </code>: esto creará un enlace - el mensaje solo mostrará <code> sometext </code>, \
y al tocarlo se abrirá la página en <code> someURL </code>.
<b> Ejemplo :</b> <código> [prueba] (ejemplo.com) </code>

• <code> [buttontext] (buttonurl: someURL) </code>: esta es una mejora especial para permitir que los usuarios tengan telegram \
botones en su rebaja. <code> buttontext </code> será lo que se muestra en el botón, y <code> someurl </code> \
será la URL que se abre.
<b> Ejemplo: </b> <code> [Este es un botón](buttonurl: example.com) </code>

Si desea varios botones en la misma línea, use: mismo, como tal:
<código> [uno](buttonurl://example.com)
[dos] (buttonurl://google.com:igual) </code>
Esto creará dos botones en una sola línea, en lugar de un botón por línea.

Tenga en cuenta que su mensaje <b> DEBE </b> contener algún texto que no sea solo un botón!
"""


@sudo_plus
def echo(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if message.reply_to_message:
        message.reply_to_message.reply_text(
            args[1], parse_mode="MARKDOWN", disable_web_page_preview=True
        )
    else:
        message.reply_text(
            args[1], quote=False, parse_mode="MARKDOWN", disable_web_page_preview=True
        )
    message.delete()


def markdown_help_sender(update: Update):
    update.effective_message.reply_text(MARKDOWN_HELP, parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(
        "Intente reenviarme el siguiente mensaje y verá, y use #test!"
    )
    update.effective_message.reply_text(
        "/save prueba Esta es una prueba de rebajas. _italics_, *bold*, code, "
        "[URL](example.com) [button](buttonurl:github.com) "
        "[button2](buttonurl://google.com:same)"
    )


def markdown_help(update: Update, context: CallbackContext):
    if update.effective_chat.type != "private":
        update.effective_message.reply_text(
            "Contáctame en pm",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Ayuda de Markdown",
                            url=f"t.me/{context.bot.username}?start=markdownhelp",
                        )
                    ]
                ]
            ),
        )
        return
    markdown_help_sender(update)


__help__ = """
*Comandos disponibles:*\n
*Covid:*
 • `/covid <país>`: proporciona la información más reciente sobre covid\n
*Tiempo:*
 • `/weather <ciudad>`: proporciona información meteorológica sobre una ubicación o un país específicos\n
*Cita:*
 • `/quotly`: responder a un mensaje para obtener un mensaje citado\n
*Markdown:*
 • `/markdownhelp`*:* resumen rápido de cómo funciona Markdown en Telegram: solo se puede llamar en chats privados\n
*Pegar:*
 • `/paste`*:* guarda el contenido respondido en `nekobin.com` y responde con una URL\n
*Reaccionar:*
 • `/react`*:* reacciona con una reacción aleatoria\n
*Diccionario urbano:*
 • `/ud <palabra>`*:* escriba la palabra o expresión que desea utilizar para buscar\n
*Wikipedia:*
 • `/wiki <consulta>`*:* wikipedia tu consulta\n
*Wallpapers:*
 • `/wall <consulta>`*:* conseguir un fondo de pantalla de wall.alphacoders.com\n
*Convertidor de moneda:* 
 • `/cash`*:* Convertidor de moneda
Ejemplo:
 `/cash 1 USD INR`  
      _OR_
 `/cash 1 usd inr`
Output: `1.0 USD = 75.505 INR`\n
*Timezones:*
 • `/time <consulta>`*:* Da información sobre una zona horaria.
*Consultas disponibles:* Código de país /Nombre de país /Nombre de zona horaria
• 🕐 [Lista de zonas horarias](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
"""

ECHO_HANDLER = DisableAbleCommandHandler("echo", echo, filters=Filters.chat_type.groups, run_async=True)
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help, run_async=True)

dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)

__mod_name__ = "Extras"
__command_list__ = ["id", "echo", "covid", "weather", "quotly"]
__handlers__ = [
    ECHO_HANDLER,
    MD_HELP_HANDLER,
]
