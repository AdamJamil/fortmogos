from __future__ import annotations

import asyncio
import atexit
import traceback
from typing import TYPE_CHECKING, Any, List

import discord
from core.data import PersistentInfo
from parse_command.help import get_help
from parse_command.manage_reminders import manage_reminders
from parse_command.set_reminder import set_reminder

from core.timer import Timer


if TYPE_CHECKING:
    from discord.message import Message
    from discord.abc import MessageableChannel


with open("token.txt", "r") as f:
    TOKEN = f.read().strip().split("\n")[0]
GUILD = "suspcious"

client = discord.Client(intents=discord.Intents.all())


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

data = PersistentInfo(client)
timer = Timer(data)


async def alert_shutdown(channels: List[MessageableChannel]):
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


def test():
    print("suspicious")


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
        data.alert_channels.append(msg.channel)
        await msg.delete()
    elif msg.content in [
        "list reminders",
        "show reminders",
        "see reminders",
        "view reminders",
    ] or msg.content.startswith("delete"):
        await manage_reminders(msg, data)


@client.event
async def on_error(event: Any, *args: Any, **kwargs: Any):
    print(
        f"The type of `event` has been found: {type(event)}. Please update the typing"
        "in `on_error`."
    )
    print(event)
    exit(1)


def get_awaitables():
    return asyncio.gather(client.start(TOKEN), timer.run())


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
