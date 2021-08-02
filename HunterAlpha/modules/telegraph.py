from HunterAlpha.event import register
from HunterAlpha import telethn as tbot
TMP_DOWNLOAD_DIRECTORY = "./"
from telethon import events
import os
from PIL import Image
from datetime import datetime
from telegraph import Telegraph, upload_file, exceptions
HunterAlpha = "HunterAlpha"
telegraph = Telegraph()
r = telegraph.create_account(short_name=HunterAlpha)
auth_url = r["auth_url"]


@register(pattern="^/t(m|xt) ?(.*)")
async def _(event):
    if event.fwd_from:
        return
    optional_title = event.pattern_match.group(2)
    if event.reply_to_msg_id:
        start = datetime.now()
        r_message = await event.get_reply_message()
        input_str = event.pattern_match.group(1)
        if input_str == "m":
            downloaded_file_name = await tbot.download_media(
                r_message,
                TMP_DOWNLOAD_DIRECTORY
            )
            end = datetime.now()
            ms = (end - start).seconds
            h = await event.reply("Descargado a {} en {} segundos.".format(downloaded_file_name, ms))
            if downloaded_file_name.endswith((".webp")):
                resize_image(downloaded_file_name)
            try:
                start = datetime.now()
                media_urls = upload_file(downloaded_file_name)
            except exceptions.TelegraphException as exc:
                await h.edit("ERROR: " + str(exc))
                os.remove(downloaded_file_name)
            else:
                end = datetime.now()
                ms_two = (end - start).seconds
                os.remove(downloaded_file_name)
                await h.edit("Subido a https://telegra.ph{})".format(media_urls[0]), link_preview=True)
        elif input_str == "xt":
            user_object = await tbot.get_entity(r_message.sender_id)
            title_of_page = user_object.first_name # + " " + user_object.last_name
            # apparently, all Users do not have last_name field
            if optional_title:
                title_of_page = optional_title
            page_content = r_message.message
            if r_message.media:
                if page_content != "":
                    title_of_page = page_content
                downloaded_file_name = await tbot.download_media(
                    r_message,
                    TMP_DOWNLOAD_DIRECTORY
                )
                m_list = None
                with open(downloaded_file_name, "rb") as fd:
                    m_list = fd.readlines()
                for m in m_list:
                    page_content += m.decode("UTF-8") + "\n"
                os.remove(downloaded_file_name)
            page_content = page_content.replace("\n", "<br>")
            response = telegraph.create_page(
                title_of_page,
                html_content=page_content
            )
            end = datetime.now()
            ms = (end - start).seconds
            await event.reply("Pegado a https://telegra.ph/{} en {} segundos.".format(response["path"], ms), link_preview=True)
    else:
        await event.reply("Responder a un mensaje para obtener un permanente. telegra.ph link.")


def resize_image(image):
    im = Image.open(image)
    im.save(image, "PNG")


__help__ = """
Puedo subir archivos a Telegraph
• `/tm` *:*Obtenga el enlace telegráfico de los medios respondidos
• `/txt`*:*Obtener enlace telegráfico del texto respondido
"""

__mod_name__ = "Telegraph"
