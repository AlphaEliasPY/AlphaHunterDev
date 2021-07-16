from datetime import datetime
from covid import Covid
from telegram import Bot, Update, ParseMode
from telegram.ext import Updater, CommandHandler
from telegram.ext import CallbackContext, run_async
from HunterAlpha import dispatcher
from HunterAlpha.modules.sql.clear_cmd_sql import get_clearcmd
from HunterAlpha.modules.helper_funcs.misc import delete


def covid(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    country = message.text[len("/covid ") :]
    covid = Covid()
    
    if country:
        try:
            country_data = covid.get_status_by_country_name(country)
        except:
            return message.reply_text("Nombre de país incorrecto!")
        
        msg = f"*Corona Virus Info*\n\n"
        msg += f"• Pais: `{country}`\n"
        msg += f"• Confirmados: `{country_data['confirmed']}`\n"
        msg += f"• Activos: `{country_data['active']}`\n"
        msg += f"• Muertos: `{country_data['deaths']}`\n"
        msg += f"• Recuperados: `{country_data['recovered']}`\n"
        msg += (
            "Last update: "
            f"`{datetime.utcfromtimestamp(country_data['last_update'] // 1000).strftime('%Y-%m-%d %H:%M:%S')}`\n"
        )
        msg += f"__Datos proporcionados por__ [Johns Hopkins University](https://j.mp/2xf6oxF)"
            
    else:
        msg = "Por favor especifique un país"

    delmsg = message.reply_text(
        text=msg,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )

    cleartime = get_clearcmd(chat.id, "covid")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


covid_handler = CommandHandler(["covid"], covid, run_async=True)
dispatcher.add_handler(covid_handler)
