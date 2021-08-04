import html
from typing import Optional, List

import HunterAlpha.modules.helper_funcs.git_api as api
import HunterAlpha.modules.sql.github_sql as sql

from HunterAlpha.modules.sql.clear_cmd_sql import get_clearcmd
from HunterAlpha import dispatcher, OWNER_ID, EVENT_LOGS, SUDO_USERS, SUPPORT_USERS
from HunterAlpha.modules.helper_funcs.filters import CustomFilters
from HunterAlpha.modules.helper_funcs.chat_status import user_admin
from HunterAlpha.modules.helper_funcs.misc import delete
from HunterAlpha.modules.disable import DisableAbleCommandHandler

from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    RegexHandler,
    run_async,
)

from telegram import (
    Message,
    Chat,
    Update,
    Bot,
    User,
    ParseMode,
    InlineKeyboardMarkup,
    MAX_MESSAGE_LENGTH,
)


def getphh(index):
    recentRelease = api.getReleaseData(api.getData("phhusson/treble_experimentations"), index)
    if recentRelease is None:
        return "No se pudo encontrar la versión especificada"
    author = api.getAuthor(recentRelease)
    authorUrl = api.getAuthorUrl(recentRelease)
    name = api.getReleaseName(recentRelease)
    assets = api.getAssets(recentRelease)
    releaseName = api.getReleaseName(recentRelease)
    message = "<b>Autor:</b> <a href='{}'>{}</a>\n".format(authorUrl, author)
    message += "<b>Liberar Name:</b> <code>"+releaseName+"</code>\n\n"
    message += "<b>Activos:</b>\n"
    for asset in assets:
        fileName = api.getReleaseFileName(asset)
        if fileName in ("manifest.xml", "patches.zip"):
            continue
        fileURL = api.getReleaseFileURL(asset)
        assetFile = "• <a href='{}'>{}</a>".format(fileURL, fileName)
        sizeB = ((api.getSize(asset))/1024)/1024
        size = "{0:.2f}".format(sizeB)
        message += assetFile + "\n"
        message += "    <code>Size: "  + size + " MB</code>\n"
    return message


# do not async
def getData(url, index):
    if not api.getData(url):
        return "Invalido <user>/<repo> combo"
    recentRelease = api.getReleaseData(api.getData(url), index)
    if recentRelease is None:
        return "No se pudo encontrar la versión especificada"
    author = api.getAuthor(recentRelease)
    authorUrl = api.getAuthorUrl(recentRelease)
    name = api.getReleaseName(recentRelease)
    assets = api.getAssets(recentRelease)
    releaseName = api.getReleaseName(recentRelease)
    message = "*Autor:* [{}]({})\n".format(author, authorUrl)
    message += "*Nombre de la versión:* " + releaseName + "\n\n"
    for asset in assets:
        message += "*Activo:* \n"
        fileName = api.getReleaseFileName(asset)
        fileURL = api.getReleaseFileURL(asset)
        assetFile = "[{}]({})".format(fileName, fileURL)
        sizeB = ((api.getSize(asset)) / 1024) / 1024
        size = "{0:.2f}".format(sizeB)
        downloadCount = api.getDownloadCount(asset)
        message += assetFile + "\n"
        message += "Size: " + size + " MB"
        message += "\nRecuento de descargas: " + str(downloadCount) + "\n\n"
    return message


# likewise, aux function, not async
def getRepo(bot, update, reponame):
    chat_id = update.effective_chat.id
    repo = sql.get_repo(str(chat_id), reponame)
    if repo:
        return repo.value, repo.backoffset
    return None, None


def getRelease(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    if len(args) == 0:
        msg.reply_text("Utilice algunos argumentos!")
        return
    if (
        len(args) != 1
        and not (len(args) == 2 and args[1].isdigit())
        and not ("/" in args[0])
    ):
        deletion(update, context, msg.reply_text("Especifique una combinación válida de <user>/<repo>"))
        return
    index = 0
    if len(args) == 2:
        index = int(args[1])
    url = args[0]
    text = getData(url, index)
    deletion(update, context, msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True))
    return


def hashFetch(update: Update, context: CallbackContext):  # kanged from notes
    bot, args = context.bot, context.args
    message = update.effective_message.text
    msg = update.effective_message
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    url, index = getRepo(bot, update, no_hash)
    if url is None and index is None:
        deletion(update, context, msg.reply_text(
            "Hubo un problema al analizar su solicitud. Es probable que este no sea un atajo de repositorio guardado",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        ))
        return
    text = getData(url, index)
    deletion(update, context, msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True))
    return


def cmdFetch(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    if len(args) != 1:
        deletion(update, context, msg.reply_text("Nombre de repositorio no válido"))
        return
    url, index = getRepo(bot, update, args[0])
    if url is None and index is None:
        deletion(update, context, msg.reply_text(
            "Hubo un problema al analizar su solicitud. Es probable que este no sea un atajo de repositorio guardado",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        ))
        return
    text = getData(url, index)
    deletion(update, context, msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True))
    return


def changelog(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    if len(args) != 1:
        deletion(update, context, msg.reply_text("Nombre de repositorio no válido"))
        return
    url, index = getRepo(bot, update, args[0])
    if not api.getData(url):
        msg.reply_text("Invalido <user>/<repo> combo")
        return
    data = api.getData(url)
    release = api.getReleaseData(data, index)
    body = api.getBody(release)
    deletion(update, context, msg.reply_text(body))
    return


@user_admin
def saveRepo(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if (
        len(args) != 2
        and (len(args) != 3 and not args[2].isdigit())
        or not ("/" in args[1])
    ):
        deletion(update, context, msg.reply_text("Datos inválidos, utilice <reponame> <user>/<repo> <valor (opcional)>"))
        return
    index = 0
    if len(args) == 3:
        index = int(args[2])
    sql.add_repo_to_db(str(chat_id), args[0], args[1], index)
    deletion(update, context, msg.reply_text("Acceso directo al repositorio guardado correctamente!"))
    return


@user_admin
def delRepo(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if len(args) != 1:
        msg.reply_text("Invalid repo name!")
        return
    sql.rm_repo(str(chat_id), args[0])
    deletion(update, context, msg.reply_text("Acceso directo al repositorio eliminado correctamente!"))
    return


def listRepo(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    chat_name = chat.title or chat.first or chat.username
    repo_list = sql.get_all_repos(str(chat_id))
    msg = "*Lista de accesos directos a repositorios en {}:*\n"
    des = "Puede obtener accesos directos a repositorios utilizando `/fetch repo`, or `&repo`.\n"
    for repo in repo_list:
        repo_name = " • `{}`\n".format(repo.name)
        if len(msg) + len(repo_name) > MAX_MESSAGE_LENGTH:
            deletion(update, context, update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN))
            msg = ""
        msg += repo_name
    if msg == "*Lista de accesos directos a repositorios en {}:*\n":
        deletion(update, context, update.effective_message.reply_text("No hay atajos de repositorio en este chat!"))
    elif len(msg) != 0:
        deletion(update, context, update.effective_message.reply_text(
            msg.format(chat_name) + des, parse_mode=ParseMode.MARKDOWN
        ))


def getVer(update: Update, context: CallbackContext):
    msg = update.effective_message
    ver = api.vercheck()
    deletion(update, context, msg.reply_text("GitHub API version: " + ver))
    return


def deletion(update: Update, context: CallbackContext, delmsg):
    chat = update.effective_chat
    cleartime = get_clearcmd(chat.id, "github")

    if cleartime:
        context.dispatcher.run_async(delete, delmsg, cleartime.time)


__help__ = """
*Módulo Github. Este módulo buscará lanzamientos de github*\n
*Comandos disponibles:*
 • `/git <user>/<repo>`: obtendrá la versión más reciente de ese repositorio.
 • `/git <user>/<repo> <numero>`: buscará lanzamientos en el pasado.
 • `/fetch <reponame> o &reponame`: igual que `/git`, pero puedes usar un atajo de repositorio guardado
 • `/listrepo`: enumera todos los accesos directos a repositorios en el chat
 • `/gitver`: devuelve la versión actual de la API
 • `/changelog <reponame>`: obtiene el registro de cambios de un acceso directo al repositorio guardado
 
*Solo administrador:*
 • `/saverepo <name> <user>/<repo> <numero (opcional)>`: guarda un valor de repositorio como acceso directo
 • `/delrepo <name>`: elimina un atajo de repositorio
"""

__mod_name__ = "GitHub"


RELEASE_HANDLER = DisableAbleCommandHandler(
    "git", getRelease, admin_ok=True, run_async=True
)
FETCH_HANDLER = DisableAbleCommandHandler(
    "fetch", cmdFetch, admin_ok=True, run_async=True
)
SAVEREPO_HANDLER = CommandHandler("saverepo", saveRepo, run_async=True)
DELREPO_HANDLER = CommandHandler("delrepo", delRepo, run_async=True)
LISTREPO_HANDLER = DisableAbleCommandHandler("listrepo", listRepo, admin_ok=True, run_async=True)
VERCHECKER_HANDLER = DisableAbleCommandHandler("gitver", getVer, admin_ok=True, run_async=True)
CHANGELOG_HANDLER = DisableAbleCommandHandler(
    "changelog", changelog, admin_ok=True, run_async=True
)

HASHFETCH_HANDLER = RegexHandler(r"^&[^\s]+", hashFetch)

dispatcher.add_handler(RELEASE_HANDLER)
dispatcher.add_handler(FETCH_HANDLER)
dispatcher.add_handler(SAVEREPO_HANDLER)
dispatcher.add_handler(DELREPO_HANDLER)
dispatcher.add_handler(LISTREPO_HANDLER)
dispatcher.add_handler(HASHFETCH_HANDLER)
dispatcher.add_handler(VERCHECKER_HANDLER)
dispatcher.add_handler(CHANGELOG_HANDLER)
