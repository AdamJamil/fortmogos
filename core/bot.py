from __future__ import annotations

import asyncio
from random import randint
import traceback
from typing import TYPE_CHECKING, Any, List, Union, cast
from discord import Member, Reaction, User
from command.misc import hijack, respond_test, subscribe_alerts

from core.data.handler import DataHandler
from core.data.writable import AlertChannel
from core.utils.arg_parse import (
    NO_TZ,
    ArgParser,
    DurationExpr,
    KleeneStar,
    Literal,
    Num,
    TimeExpr,
    TimeZoneExpr,
    Warn,
)
from core.utils.color import green, red
from core.utils.constants import warning_emoji
from core.utils.exceptions import MissingTimezoneException
from command.manage_wakeup import (
    change_wakeup_time,
    disable,
    enable,
    init_wakeup,
    set_channel,
)
from command.manage_reaction import manage_reaction
from command.help import help_reminder
from command.manage_reminder import delete_reminder, show_reminders
from command.manage_task import add_task, delete_task, show_tasks
from command.manage_timezone import manage_timezone
from command.set_reminder import set_daily, set_in
from core.utils.constants import get_token, sep, client
from core.timer import Timer


if TYPE_CHECKING:
    from discord.message import Message

data = DataHandler()
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


SHOW = ("list", "show", "see", "view")
DELETE = ("delete", "remove")
TASKS = ("task", "tasks", "todo", "todos")
REMINDERS = ("reminder", "reminders")

arg_parser = ArgParser(
    NO_TZ() >> Literal("help reminder") >> help_reminder,
    NO_TZ() >> Literal("timezone") >> TimeZoneExpr() >> manage_timezone,
    NO_TZ() >> Literal("subscribe alerts") >> subscribe_alerts,
    NO_TZ() >> Literal("With a hey, ho") >> respond_test,
    Literal(SHOW, TASKS) >> show_tasks,
    Literal(DELETE, TASKS) >> Num() >> delete_task,
    Literal(SHOW, REMINDERS) >> show_reminders,
    Literal(DELETE, REMINDERS) >> Num() >> delete_reminder,
    Literal("exec") >> KleeneStar() >> hijack,
    Literal(TASKS) >> KleeneStar() >> add_task,
    Literal("wakeup disable") >> disable,
    Literal("wakeup enable") >> enable,
    Literal("wakeup set") >> set_channel,
    Literal("wakeup") >> TimeExpr() >> change_wakeup_time,
)

# mypy has a stroke when chaining more than one Expr1...
daily_cmd: Any = Literal("daily") >> TimeExpr()
shit: Any = KleeneStar()
daily_cmd >>= shit
daily_cmd >>= set_daily

in_cmd: Any = Literal("in") >> DurationExpr()
shit2: Any = KleeneStar()
in_cmd >>= shit2
in_cmd >>= set_in

arg_parser.commands.extend((daily_cmd, in_cmd))


@client.event
async def on_message(msg: Message):
    if msg.author.id in (1061719682773688391, 1074389982095089664):
        return
    if msg.author.id == 267807519286624258:
        if randint(1, 4) == 1:
            await msg.add_reaction("🍆")
    try:
        parsed_command = arg_parser.parse_message(msg.content)

        if parsed_command.needs_tz and msg.author.id not in data.timezones.keys():
            raise MissingTimezoneException()

        if isinstance(parsed_command.res, list):  # warning
            await msg.add_reaction(warning_emoji)
        elif isinstance(parsed_command.res, tuple):  # args
            await parsed_command.f(msg, data, *parsed_command.res)

        if msg.author.id not in data.wakeup and any(
            todo.user_id == msg.author.id for todo in data.user_tasks
        ):
            await init_wakeup(msg.author.id, msg.channel.id, data)
    except MissingTimezoneException:
        await msg.add_reaction(warning_emoji)
    except Exception as e:
        red(f"Wtf:\n{e}\n{traceback.format_exc()}")
        await msg.reply(f"Something broke:\n{e}\n{traceback.format_exc()}")


@client.event
async def on_reaction_add(reaction: Reaction, user: Union[Member, User]):
    if str(user.id) in reaction.message.content:
        await manage_reaction(reaction, user, data)
    elif user.id == reaction.message.author.id and str(reaction.emoji) == warning_emoji:
        async for user in reaction.users():
            if user.id in (1061719682773688391, 1074389982095089664):
                await reaction.message.remove_reaction(warning_emoji, user)
                parsed_command = arg_parser.parse_message(reaction.message.content)
                if (
                    parsed_command.needs_tz
                    and reaction.message.author.id not in data.timezones.keys()
                ):
                    await reaction.message.reply(MissingTimezoneException().help)
                else:
                    await reaction.message.reply(
                        cast(List[Warn], parsed_command.res)[0],
                    )
                break

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
