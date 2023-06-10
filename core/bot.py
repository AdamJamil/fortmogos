from __future__ import annotations

import asyncio
import traceback
from typing import TYPE_CHECKING, Any, List, Union
from discord import Member, Reaction, User

from core.data.handler import DataHandler
from core.data.writable import AlertChannel
from core.utils.color import green, red
from core.utils.exceptions import MissingTimezoneException
from parse_command.manage_wakeup import init_wakeup, parse_wakeup
from parse_command.manage_reaction import manage_reaction
from parse_command.help import get_help
from parse_command.manage_reminder import manage_reminder
from parse_command.manage_task import add_task, delete_task, show_tasks
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


def manage_reminder_check(msg: Message):
    return (
        msg.content
        in [
            "list reminders",
            "show reminders",
            "see reminders",
            "view reminders",
        ]
        or msg.content.startswith("delete reminder ")
        or msg.content.startswith("remove reminder ")
    )


@client.event
async def on_message(msg: Message):
    if msg.author.id in (1061719682773688391, 1089042918259564564):
        return
    try:
        channel = msg.channel.id
        if msg.content == "With a hey, ho":
            await msg.reply(":notes: the wind and the rain :notes:")
            return
        elif msg.content.startswith("help "):
            await get_help(msg)
        elif msg.content.startswith("timezone "):
            await manage_timezone(msg, data)
        elif msg.content == "subscribe alerts":
            await msg.reply(
                f"Got it, <@{msg.author.id}>. This channel will now be used "
                "to send alerts out regarding the state of the bot."
            )
            data.alert_channels.append(AlertChannel(msg.channel))
            await msg.delete()
        elif msg.content in [
            "list tasks",
            "show tasks",
            "see tasks",
            "view tasks",
            "list todo",
            "show todo",
            "see todo",
            "view todo",
        ]:
            await show_tasks(msg, data)
        elif msg.content.startswith("delete task ") or msg.content.startswith(
            "delete todo "
        ):
            await delete_task(msg, data)
        elif msg.content.startswith("exec"):
            exec(msg.content[6:-2])
        elif (
            msg.content.startswith("daily ")
            or msg.content.startswith("weekly ")
            or msg.content.startswith("in ")
            or manage_reminder_check(msg)
            or msg.content.startswith("task ") or msg.content.startswith("todo ")
            or msg.content.startswith("wakeup ")
        ):
            if msg.author.id not in data.timezones.keys():
                raise MissingTimezoneException()
            if manage_reminder_check(msg):
                await manage_reminder(msg, data)
            elif msg.content.startswith("task ") or msg.content.startswith("todo "):
                await add_task(msg, data)
            elif msg.content.startswith("wakeup "):
                await parse_wakeup(msg, data)
            else:
                await set_reminder(msg, data, client)

        if msg.author.id not in data.wakeup and any(
            todo.user_id == msg.author.id for todo in data.user_tasks
        ):
            await init_wakeup(msg.author.id, channel, data)

    except MissingTimezoneException as e:
        await msg.reply(e.help)
    except Exception as e:
        red(f"Wtf:\n{e}\n{traceback.format_exc()}")
        await msg.reply(f"Something broke:\n{e}\n{traceback.format_exc()}")


@client.event
async def on_reaction_add(reaction: Reaction, user: Union[Member, User]):
    if str(user.id) in reaction.message.content:
        await manage_reaction(reaction, user, data)

    if user.id not in data.wakeup and any(
        todo.user_id == user.id for todo in data.user_tasks
    ):
        await init_wakeup(user.id, reaction.message.channel.id, data)


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
