from __future__ import annotations

from random import choice, randint
import traceback
from typing import TYPE_CHECKING, Any, List, Union, cast
from discord import Member, Reaction, User
from core.command_processor import CommandProcessor

from core.utils.parse import (
    Warn,
)
from core.utils.color import red
from core.utils.constants import warning_emoji
from core.utils.exceptions import MissingTimezoneException
from command.manage_wakeup import (
    init_wakeup,
)
from disc.manage_reaction import manage_reaction
from disc.context import DiscordMessageContext, DiscordReactionContext
from core.utils.constants import sep, client
from core.start import data

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
    data.populate_data()


command_processor = CommandProcessor()


@client.event
async def on_message(msg: Message):
    if msg.author.id in (1061719682773688391, 1074389982095089664):
        return
    if msg.author.id == 267807519286624258:
        if randint(1, 12) == 1:
            await msg.add_reaction(choice(["🍆", "💦", "🍑", "😳"]))
    try:
        await command_processor.parse_and_respond(DiscordMessageContext(msg))
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
                parsed_command = command_processor.arg_parser.parse_message(
                    reaction.message.content
                )
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
        await init_wakeup(DiscordReactionContext(reaction, user), data)


@client.event
async def on_error(event: str, *args: Any, **kwargs: Any):
    red(f"Discord threw an exception:\n{sep.ins('event')}")
    red(event)
    red(sep.ins("args"))
    red(args)
    red(sep.ins("kwargs"))
    red(kwargs)
    exit(1)
