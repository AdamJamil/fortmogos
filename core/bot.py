from __future__ import annotations

import asyncio
import atexit
import traceback
from typing import TYPE_CHECKING, Any, List

from core.data.handler import DataHandler
from core.data.writable import AlertChannel
from core.utils.color import red
from parse_command.help import get_help
from parse_command.manage_reminder import manage_reminder
from parse_command.set_reminder import set_reminder
from core.utils.constants import sep, client, FAKE_TOKEN
from core.timer import Timer


if TYPE_CHECKING:
    from discord.message import Message


@client.event
async def on_ready():
    if not client.guilds:
        print(f"{client.user} is not connected to any guilds.")
    else:
        print(
            f"{client.user} is connected to "
            f"{', '.join(guild.name for guild in client.guilds)}."
        )


help_messages = []

data = DataHandler(client)
timer = Timer(data)


async def alert_shutdown(channels: List[AlertChannel]):
    await asyncio.gather(*(channel.send("zzz") for channel in channels))


@atexit.register
def shutdown() -> None:
    """
    This function is run when the bot shuts down.
    Subscribed channels are alerted and data is saved.
    """
    if data.alert_channels:
        asyncio.run(alert_shutdown(data.alert_channels))
        print("Sent channel alerts.")


@client.event
async def on_message(msg: Message):
    if msg.author.id == 1061719682773688391:
        return
    if msg.content == "With a hey, ho":
        await msg.reply(":notes: the wind and the rain :notes:")
    elif msg.content.startswith("help "):
        await get_help(msg)
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
    ] or msg.content.startswith("delete"):
        await manage_reminder(msg, data)


@client.event
async def on_error(event: str, *args: Any, **kwargs: Any):
    red(f"Discord threw an exception:\n{sep.ins('event')}")
    red(event)
    red(sep.ins("args"))
    red(args)
    red(sep.ins("kwargs"))
    red(kwargs)
    exit(1)


def get_awaitables():
    return asyncio.gather(client.start(FAKE_TOKEN), timer.run())


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
        exit(1)


if __name__ == "__main__":
    main()
