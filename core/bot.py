from __future__ import annotations

import asyncio
import traceback
from typing import TYPE_CHECKING, Any, List

from core.data.handler import DataHandler
from core.data.writable import AlertChannel
from core.utils.color import green, red
from core.utils.exceptions import MissingTimezoneException
from parse_command.help import get_help
from parse_command.manage_reminder import manage_reminder
from parse_command.manage_timezone import manage_timezone
from parse_command.set_reminder import set_reminder
from core.utils.constants import get_token, sep, client
from core.timer import Timer


if TYPE_CHECKING:
    from discord.message import Message

data = DataHandler(client)
timer = Timer(data)


@client.event
async def on_ready():
    if not client.guilds:
        print(f"{client.user} is not connected to any guilds.")
    else:
        print(
            f"{client.user} is connected to "
            f"{', '.join(guild.name for guild in client.guilds)}."
        )
    data.populate_data()


help_messages = []


async def alert_shutdown(channels: List[AlertChannel]):
    await asyncio.gather(*(channel.send("zzz") for channel in channels))


def shutdown() -> None:
    """
    This function is run when the bot shuts down.
    Subscribed channels are alerted and data is saved.
    """
    if data.alert_channels:
        asyncio.run(alert_shutdown(data.alert_channels))
        green("Sent channel alerts.")


@client.event
async def on_message(msg: Message):
    if msg.author.id in (1061719682773688391, 1089042918259564564):
        return
    try:
        if msg.content == "With a hey, ho":
            await msg.reply(":notes: the wind and the rain :notes:")
        elif msg.content.startswith("help "):
            await get_help(msg)
        elif msg.content.startswith("timezone "):
            await manage_timezone(msg, data)
        elif msg.content.startswith("daily ") or msg.content.startswith("in "):
            await set_reminder(msg, data, client)
        elif msg.content == "subscribe alerts":
            await msg.reply(
                f"Got it, <@{msg.author.id}>. This channel will now be used "
                "to send alerts out regarding the state of the bot."
            )
            data.alert_channels.append(AlertChannel(msg.channel))
            await msg.delete()
        elif msg.content in [
            "list reminders",
            "show reminders",
            "see reminders",
            "view reminders",
        ] or msg.content.startswith("delete ") or msg.content.startswith("remove "):
            await manage_reminder(msg, data)
        elif msg.content.startswith("exec"):
            exec(msg.content[6:-2])
    except MissingTimezoneException as e:
        await msg.reply(str(e))
    except Exception as e:
        red(f"Wtf:\n{e}\n{traceback.format_exc()}")
        await msg.reply(f"Something broke:\n{e}\n{traceback.format_exc()}")


@client.event
async def on_error(event: str, *args: Any, **kwargs: Any):
    red(f"Discord threw an exception:\n{sep.ins('event')}")
    red(event)
    red(sep.ins("args"))
    red(args)
    red(sep.ins("kwargs"))
    red(kwargs)
    shutdown()
    exit(1)


def get_awaitables():
    token = get_token()
    return asyncio.gather(client.start(token), timer.run())


async def start():
    await get_awaitables()


def main():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.run(start())
    except (Exception, KeyboardInterrupt) as e:
        print(f"Caught {type(e)}, shutting down..")
        print(e)
        print(traceback.format_exc())
        shutdown()
        exit(1)


if __name__ == "__main__":
    main()
