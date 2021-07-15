# Magisk Module- Module from AstrakoBot
# Inspired from RaphaelGang's android.py
# By DAvinash97


from datetime import datetime
from bs4 import BeautifulSoup
from requests import get
from telegram import Bot, Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import CallbackContext, run_async
from ujson import loads
from yaml import load, Loader

from HunterAlpha import dispatcher
from HunterAlpha.modules.sql.clear_cmd_sql import get_clearcmd
from HunterAlpha.modules.github import getphh
from HunterAlpha.modules.helper_funcs.misc import delete


def magisk(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    link = "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/"
    magisk_dict = {
        "*Stable*": "stable.json",
        "\n" "*Canary*": "canary.json",
    }.items()
    msg = "*Últimos lanzamientos de Magisk:*\n\n"
    for magisk_type, release_url in magisk_dict:
        data = get(link + release_url).json()
        msg += (
            f"{magisk_type}:\n"
            f'• Manager - [{data["magisk"]["version"]} ({data["magisk"]["versionCode"]})]({data["magisk"]["link"]}) \n'
        )

    delmsg = message.reply_text(
        text = msg,
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

    cleartime = get_clearcmd(chat.id, "magisk")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


def checkfw(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    
    if len(args) == 2:
        temp, csc = args
        model = f'sm-' + temp if not temp.upper().startswith('SM-') else temp
        fota = get(
            f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.xml'
        )

        if fota.status_code != 200:
            msg = f"No se pudo verificar {temp.upper()} y {csc.upper()}, refina tu búsqueda o vuelve a intentarlo más tarde!"

        else:
            page = BeautifulSoup(fota.content, 'lxml')
            os = page.find("latest").get("o")

            if page.find("latest").text.strip():
                msg = f'*Firmware lanzado más reciente para {model.upper()} y {csc.upper()} es:*\n'
                pda, csc, phone = page.find("latest").text.strip().split('/')
                msg += f'• PDA: `{pda}`\n• CSC: `{csc}`\n'
                if phone:
                    msg += f'• Movil: `{phone}`\n'
                if os:
                    msg += f'• Android: `{os}`\n'
                msg += ''
            else:
                msg = f'*No se encontró ningún comunicado público para {model.upper()} y {csc.upper()}.*\n\n'

    else:
        msg = 'Dame algo para traer, como:\n`/checkfw SM-N975F DBT`'

    delmsg = message.reply_text(
        text = msg,
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

    cleartime = get_clearcmd(chat.id, "checkfw")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


def getfw(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    btn = ""
    
    if len(args) == 2:
        temp, csc = args
        model = f'sm-' + temp if not temp.upper().startswith('SM-') else temp
        fota = get(
            f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.xml'
        )

        if fota.status_code != 200:
            msg = f"No se pudo verificar {temp.upper()} y {csc.upper()}, refina tu búsqueda o vuelve a intentarlo más tarde!"

        else:
            url1 = f'https://samfrew.com/model/{model.upper()}/region/{csc.upper()}/'
            url2 = f'https://www.sammobile.com/samsung/firmware/{model.upper()}/{csc.upper()}/'
            url3 = f'https://sfirmware.com/samsung-{model.lower()}/#tab=firmwares'
            url4 = f'https://samfw.com/firmware/{model.upper()}/{csc.upper()}/'
            fota = get(
                f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.xml'
            )
            page = BeautifulSoup(fota.content, 'lxml')
            os = page.find("latest").get("o")
            msg = ""
            if page.find("latest").text.strip():
                pda, csc2, phone = page.find("latest").text.strip().split('/')
                msg += f'*Firmware más reciente para {model.upper()} and {csc.upper()} is:*\n'
                msg += f'• PDA: `{pda}`\n• CSC: `{csc2}`\n'
                if phone:
                    msg += f'• Movil: `{phone}`\n'
                if os:
                    msg += f'• Android: `{os}`\n'
            msg += '\n'
            msg += f'*Descargas para {model.upper()} and {csc.upper()}*\n'
            btn = [[InlineKeyboardButton(text=f"samfrew.com", url = url1)]]
            btn += [[InlineKeyboardButton(text=f"sammobile.com", url = url2)]]
            btn += [[InlineKeyboardButton(text=f"sfirmware.com", url = url3)]]
            btn += [[InlineKeyboardButton(text=f"samfw.com", url = url4)]]
    else:
        msg = 'Dame algo para traer, como:\n`/getfw SM-N975F DBT`'

    delmsg = message.reply_text(
        text = msg,
        reply_markup = InlineKeyboardMarkup(btn),
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

    cleartime = get_clearcmd(chat.id, "getfw")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


def phh(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    index = int(args[0]) if len(args) > 0 and args[0].isdigit() else 0
    text = getphh(index)

    delmsg = message.reply_text(
        text,
        parse_mode = ParseMode.HTML,
        disable_web_page_preview = True,
    )

    cleartime = get_clearcmd(chat.id, "phh")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


def miui(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    device = message.text[len("/miui ") :]
    markup = []

    if device:
        link = "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/data/latest.yml"
        yaml_data = load(get(link).content, Loader=Loader)
        data = [i for i in yaml_data if device in i['codename']]

        if not data:
            msg = f"Miui no está disponible para {device}"
        else:
            for fw in data:
                av = fw['android']
                branch = fw['branch']
                method = fw['method']
                link = fw['link']
                fname = fw['name']
                version = fw['version']
                size = fw['size']
                btn = fname + ' | ' + branch + ' | ' + method + ' | ' + version + ' | ' + av + ' | ' + size
                markup.append([InlineKeyboardButton(text = btn, url = link)])

            device = fname.split(" ")
            device.pop()
            device = " ".join(device)
            msg = f"Los últimos firmwares para *{device}* estan:"
    else:
        msg = 'Dame algo para traer, como:\n`/miui whyred`'

    delmsg = message.reply_text(
        text = msg,
        reply_markup = InlineKeyboardMarkup(markup),
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

    cleartime = get_clearcmd(chat.id, "miui")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


def orangefox(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    device = message.text[len("/orangefox ") :]
    btn = ""

    if device:
        link = get(f"https://api.orangefox.download/v3/releases/?codename={device}&sort=date_desc&limit=1")

        if link.status_code == 404:
            msg = f"La recuperación de OrangeFox no está disponible para {device}"
        else:
            page = loads(link.content)
            file_id = page["data"][0]["_id"]
            link = get(f"https://api.orangefox.download/v3/devices/get?codename={device}")
            page = loads(link.content)
            oem = page["oem_name"]
            model = page["model_name"]
            full_name = page["full_name"]
            maintainer = page["maintainer"]["username"]
            link = get(f"https://api.orangefox.download/v3/releases/get?_id={file_id}")
            page = loads(link.content)
            dl_file = page["filename"]
            build_type = page["type"]
            version = page["version"]
            changelog = page["changelog"][0]
            size = str(round(float(page["size"]) / 1024 / 1024, 1)) + "MB"
            dl_link = page["mirrors"]["DL"]
            date = datetime.fromtimestamp(page["date"])
            md5 = page["md5"]
            msg = f"*La última recuperación de OrangeFox para {full_name}*\n\n"
            msg += f"• Manufacturer: `{oem}`\n"
            msg += f"• Model: `{model}`\n"
            msg += f"• Codename: `{device}`\n"
            msg += f"• Build type: `{build_type}`\n"
            msg += f"• Maintainer: `{maintainer}`\n"
            msg += f"• Version: `{version}`\n"
            msg += f"• Changelog: `{changelog}`\n"
            msg += f"• Size: `{size}`\n"
            msg += f"• Date: `{date}`\n"
            msg += f"• File: `{dl_file}`\n"
            msg += f"• MD5: `{md5}`\n"
            btn = [[InlineKeyboardButton(text=f"Descargar", url = dl_link)]]
    else:
        msg = 'Dame algo para traer, like:\n`/orangefox a3y17lte`'

    delmsg = message.reply_text(
        text = msg,
        reply_markup = InlineKeyboardMarkup(btn),
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

    cleartime = get_clearcmd(chat.id, "orangefox")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


def twrp(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    device = message.text[len("/twrp ") :]
    btn = ""

    if device:
        link = get(f"https://eu.dl.twrp.me/{device}")

        if link.status_code == 404:
            msg = f"TWRP no está disponible para {device}"
        else:
            page = BeautifulSoup(link.content, "lxml")
            download = page.find("table").find("tr").find("a")
            dl_link = f"https://eu.dl.twrp.me{download['href']}"
            dl_file = download.text
            size = page.find("span", {"class": "filesize"}).text
            date = page.find("em").text.strip()
            msg = f"*Último TWRP para {device}*\n\n"
            msg += f"• Size: `{size}`\n"
            msg += f"• Date: `{date}`\n"
            msg += f"• File: `{dl_file}`\n\n"
            btn = [[InlineKeyboardButton(text=f"Descargar", url = dl_link)]]
    else:
        msg = 'Dame algo para traer, como:\n`/twrp a3y17lte`'

    delmsg = message.reply_text(
        text = msg,
        reply_markup = InlineKeyboardMarkup(btn),
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

    cleartime = get_clearcmd(chat.id, "twrp")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


__help__ = """
*Comandos disponibles:*\n
*Magisk:* 
• `/magisk`, `/su`, `/root`: obtiene el último magisk\n
*Proyecto de recovery OrangeFox:* 
• `/orangefox` `<nombre de dispositivo>`: obtiene la última recuperación de OrangeFox disponible para un nombre en clave de dispositivo dado\n
*TWRP:* 
• `/twrp <nombre de dispositivo>`: obtiene el TWRP más reciente disponible para un nombre en clave de dispositivo dado\n
*MIUI:*
• `/miui <nombre de dispositivo>`- obtiene la información de firmware más reciente para un nombre en clave de dispositivo dado\n
*Phh:* 
• `/phh`: obtener las últimas compilaciones de phh de github\n
*Samsung:*
• `/checkfw <modelo> <csc>` - Samsung solamente - muestra la información de firmware más reciente para el dispositivo dado, tomada de los servidores de Samsung
• `/getfw <modelo> <csc>` - Samsung solamente - obtiene enlaces de descarga de firmware de samfrew, sammobile y sfirmwares para el dispositivo dado
"""

MAGISK_HANDLER = CommandHandler(["magisk", "root", "su"], magisk, run_async=True)
ORANGEFOX_HANDLER = CommandHandler("orangefox", orangefox, run_async=True)
TWRP_HANDLER = CommandHandler("twrp", twrp, run_async=True)
GETFW_HANDLER = CommandHandler("getfw", getfw, run_async=True)
CHECKFW_HANDLER = CommandHandler("checkfw", checkfw, run_async=True)
PHH_HANDLER = CommandHandler("phh", phh, run_async=True)
MIUI_HANDLER = CommandHandler("miui", miui, run_async=True)


dispatcher.add_handler(MAGISK_HANDLER)
dispatcher.add_handler(ORANGEFOX_HANDLER)
dispatcher.add_handler(TWRP_HANDLER)
dispatcher.add_handler(GETFW_HANDLER)
dispatcher.add_handler(CHECKFW_HANDLER)
dispatcher.add_handler(PHH_HANDLER)
dispatcher.add_handler(MIUI_HANDLER)

__mod_name__ = "Android"
__command_list__ = ["magisk", "root", "su", "orangefox", "twrp", "checkfw", "getfw", "phh", "miui"]
__handlers__ = [MAGISK_HANDLER, ORANGEFOX_HANDLER, TWRP_HANDLER, GETFW_HANDLER, CHECKFW_HANDLER, PHH_HANDLER, MIUI_HANDLER]
