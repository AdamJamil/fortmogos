import asyncio
import atexit
from typing import TYPE_CHECKING

import discord
from core.data import PersistentInfo
from parse_command.help import get_help
from parse_command.manage_reminders import manage_reminders
from parse_command.set_reminder import set_reminder

from core.timer import Timer


if TYPE_CHECKING:
    from discord.message import Message


with open("token.txt", "r") as f:
    TOKEN = f.read().strip()
GUILD = "suspcious"

client = discord.Client(intents=discord.Intents.all())


@client.event
async def on_ready():
    guild = None
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    if guild is None:
        print("No guild detected.")
        return

    print(
        f"{client.user} is connected to the following guild:\n"
        f"{guild.name}(id: {guild.id})"
    )


help_messages = []

data = PersistentInfo(client)
timer = Timer(data)


@atexit.register
def shutdown() -> None:
    """
    This function is run when the bot shuts down.
    Subscribed channels are alerted and data is saved.
    """
    if alert_channels := data.save():
        loop.run_until_complete(
            asyncio.gather(*(channel.send("zzz") for channel in alert_channels))
        )
    print("Saved data.")


@client.event
async def on_message(msg: "Message"):
    if msg.author.id == 1061719682773688391:
        return
    if msg.content.startswith("help "):
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


try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(client.start(TOKEN), timer.run()))
except (Exception, KeyboardInterrupt) as e:
    print(f"Caught {type(e)}, shutting down..")
    print(e)
    exit(1)
