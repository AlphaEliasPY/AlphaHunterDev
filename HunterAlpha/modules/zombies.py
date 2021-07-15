from asyncio import sleep
from telethon import events
from HunterAlpha import dispatcher
from HunterAlpha import telethn as HunterAlphaTelethonClient
from HunterAlpha.modules.sql.clear_cmd_sql import get_clearcmd
from HunterAlpha.modules.helper_funcs.telethn.chatstatus import user_is_admin
from HunterAlpha.modules.helper_funcs.misc import delete


@HunterAlphaTelethonClient.on(events.NewMessage(pattern=f"^[!/]zombies ?(.*)"))
async def zombies(event):
    chat = await event.get_chat()
    chat_id = event.chat_id
    admin = chat.admin_rights
    creator = chat.creator

    if not await user_is_admin(
        user_id = event.sender_id, message = event
    ):
        delmsg = "Solo los administradores pueden usar este comando."

    elif not admin and not creator:
        delmsg = "I am not an admin here!"

    else:

        count = 0
        arg = event.pattern_match.group(1).lower()

        if not arg:
                msg = "**Buscando zombies...**\n"
                msg = await event.reply(msg)
                async for user in event.client.iter_participants(event.chat):
                    if user.deleted:
                        count += 1

                if count == 0:
                    delmsg = await msg.edit("No se encontraron cuentas eliminadas. El grupo está limpio")
                else:
                    delmsg = await msg.edit(f"Encontrado **{count}** zombis en este grupo\nLimpiarlos usando - `/zombies clean`")
        
        elif arg == "clean":
            msg = "**limpieza de zombies...**\n"
            msg = await event.reply(msg)
            async for user in event.client.iter_participants(event.chat):
                if user.deleted and not await user_is_admin(user_id = user, message = event):
                    count += 1
                    await event.client.kick_participant(chat, user)

            if count == 0:
                delmsg = await msg.edit("No se encontraron cuentas eliminadas. El grupo está limpio")
            else:
                delmsg = await msg.edit(f"Limpiado `{count}` zombies")
      
        else:
            delmsg = await event.reply("Parámetro incorrecto. Puedes usar solo `/zombies clean`")


    cleartime = get_clearcmd(chat_id, "zombies")

    if cleartime:
        await sleep(cleartime.time)
        await delmsg.delete()

