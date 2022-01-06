from emoji import UNICODE_EMOJI
from google_trans_new import LANGUAGES, google_translator
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, run_async

from HunterAlpha import dispatcher
from HunterAlpha.modules.disable import DisableAbleCommandHandler
from HunterAlpha.modules.helper_funcs.misc import delete
from HunterAlpha.modules.sql.clear_cmd_sql import get_clearcmd


def totranslate(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    problem_lang_code = []
    text = ""
    for key in LANGUAGES:
        if "-" in key:
            problem_lang_code.append(key)

    try:
        if message.reply_to_message:
            args = update.effective_message.text.split(None, 1)
            if message.reply_to_message.text:
                text = message.reply_to_message.text
            elif message.reply_to_message.caption:
                text = message.reply_to_message.caption

            try:
                source_lang = args[1].split(None, 1)[0]
            except (IndexError, AttributeError):
                source_lang = "en"

        else:
            args = update.effective_message.text.split(None, 2)
            text = args[2]
            source_lang = args[1]

        if source_lang.count("-") == 2:
            for lang in problem_lang_code:
                if lang in source_lang:
                    if source_lang.startswith(lang):
                        dest_lang = source_lang.rsplit("-", 1)[1]
                        source_lang = source_lang.rsplit("-", 1)[0]
                    else:
                        dest_lang = source_lang.split("-", 1)[1]
                        source_lang = source_lang.split("-", 1)[0]
        elif source_lang.count("-") == 1:
            for lang in problem_lang_code:
                if lang in source_lang:
                    dest_lang = source_lang
                    source_lang = None
                    break
            if dest_lang is None:
                dest_lang = source_lang.split("-")[1]
                source_lang = source_lang.split("-")[0]
        else:
            dest_lang = source_lang
            source_lang = None

        exclude_list = UNICODE_EMOJI.keys()
        for emoji in exclude_list:
            if emoji in text:
                text = text.replace(emoji, "")

        trl = google_translator()
        if source_lang is None:
            detection = trl.detect(text)
            trans_str = trl.translate(text, lang_tgt=dest_lang)
            delmsg = message.reply_text(
                f"Traducido de `{detection[0]}` a `{dest_lang}`:\n`{trans_str}`",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            trans_str = trl.translate(text, lang_tgt=dest_lang, lang_src=source_lang)
            delmsg = message.reply_text(
                f"Traducido de `{source_lang}` a `{dest_lang}`:\n`{trans_str}`",
                parse_mode=ParseMode.MARKDOWN,
            )

        deletion(update, context, delmsg)

    except IndexError:
        delmsg = update.effective_message.reply_text(
            "Responder a mensajes o escribir mensajes en otros idiomas ​​para traducir al idioma deseado\n\n"
            "Ejemplo: `/tr en-ml` traducir del inglés al malayalam\n"
            "O use: `/tr ml` para la detección automática y su traducción al malayalam.\n"
            "Ver [Lista de códigos de idioma](https://telegra.ph/%F0%9D%94%BC%F0%9D%95%9D-%F0%9D%94%B9%F0%9D%95%A3%F0%9D%95%A0%F0%9D%95%9E%F0%9D%95%92%F0%9D%95%A4-08-01) para obtener una lista de códigos de idioma.",
            parse_mode="markdown",
            disable_web_page_preview=True,
        )
        deletion(update, context, delmsg)
    except ValueError:
        delmsg = update.effective_message.reply_text("No se encuentra el idioma deseado!")
        deletion(update, context, delmsg)
    else:
        return


def deletion(update: Update, context: CallbackContext, delmsg):
    chat = update.effective_chat
    cleartime = get_clearcmd(chat.id, "tr")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


__help__ = """
• `/tr` or `/tl` (código de idioma) como respuesta a un mensaje largo
*Ejemplo:* 
  `/tr en`*:* traduce algo al ingles
  `/tr hi-en`*:* traduce del hindi al inglés
"""

TRANSLATE_HANDLER = DisableAbleCommandHandler(["tr", "tl"], totranslate, run_async=True)

dispatcher.add_handler(TRANSLATE_HANDLER)

__mod_name__ = "Traductor"
__command_list__ = ["tr", "tl"]
__handlers__ = [TRANSLATE_HANDLER]
