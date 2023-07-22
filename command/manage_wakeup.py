from __future__ import annotations

from typing import cast
from datetime import time as Time
import discord
import pytz
from pytz import utc

from core.data.handler import DataHandler
from core.data.writable import Wakeup
from core.utils.time import logical_time_repr, tz_convert_time
from core.utils.constants import client


# TODO: Maybe call this from a wakeup help method?
# def wakeup_status(user: int) -> str:
#     if user not in data.wakeup:
#         return "Not set up."
#     elif cast(bool, data.wakeup[user].disabled):
#         return "Disabled."
#     else:
#         time_str = logical_time_repr(data.wakeup[user].time, data.timezones[user].tz)
#         return f"Enabled daily at {time_str}."


def default_wakeup(user: int, data: DataHandler) -> Time:
    return (
        Time(hour=6)
        if user not in data.timezones
        else tz_convert_time(Time(hour=6), data.timezones[user].tz, pytz.utc)
    )


async def init_wakeup(user: int, channel: int, data: DataHandler) -> None:
    await client.get_partial_messageable(channel).send(
        f"Daily pings with your todo list will appear here, <@{user}>!\n"
        "`wakeup <time>` changes the time, `wakeup set` resets the channel, and "
        "`wakeup disable` shuts it up."
    )
    data.wakeup[user] = Wakeup(user, default_wakeup(user, data), channel)


async def enable(msg: discord.message.Message, data: DataHandler) -> None:
    user = msg.author.id
    if user not in data.wakeup:
        data.wakeup[user] = Wakeup(user, default_wakeup(user, data), msg.channel.id)
        await msg.reply(
            f"Daily pings with your todo list will appear here, <@{user}>!\n"
            "`wakeup <time>` changes the time, `wakeup set` resets the channel, and "
            "`wakeup disable` shuts it up."
        )
    elif cast(bool, data.wakeup[user].disabled):
        await msg.reply("Re-enabled your daily todo reminders.")
    else:
        await msg.reply("Already enabled, galaxy brain.")
    await msg.delete()


async def disable(msg: discord.message.Message, data: DataHandler) -> None:
    user = msg.author.id
    if user not in data.wakeup:
        data.wakeup[user] = Wakeup(
            user,
            default_wakeup(user, data),
            msg.channel.id,
            disabled=True,
        )
        await msg.reply(
            "You don't have a wakeup set. Setting and disabling one. "
            "You can undo this with `wakeup enable`."
        )
        await msg.delete()
    elif cast(bool, data.wakeup[user].disabled):
        await msg.reply("It's already disabled, galaxy brain.")
        await msg.delete()
    else:
        await msg.reply(
            f"Got it, <@{user}>, you will no longer "
            "receive daily todo reminders. You can undo this with `wakeup enable`."
        )
        await msg.delete()
        data.wakeup[user] = Wakeup(
            user,
            data.wakeup[user].time,
            cast(int, data.wakeup[user].channel),
            disabled=True,
        )


async def set_channel(msg: discord.message.Message, data: DataHandler) -> None:
    user = msg.author.id
    if user not in data.wakeup:
        data.wakeup[user] = Wakeup(user, default_wakeup(user, data), msg.channel.id)
        await msg.reply(
            f"Daily pings with your todo list will appear here, <@{user}>!\n"
            "`wakeup <time>` changes the time, `wakeup set` resets the channel, and "
            "`wakeup disable` shuts it up."
        )
        await msg.delete()
    else:
        await msg.reply(
            f"Got it, <@{user}>, your daily todo list will appear here now."
        )
        await msg.delete()


async def change_wakeup_time(
    msg: discord.message.Message,
    data: DataHandler,
    new_wakeup: Time,
) -> None:
    tz = data.timezones[msg.author.id].tz
    new_wakeup = tz_convert_time(new_wakeup, tz, utc)
    user = msg.author.id
    if user not in data.wakeup:
        data.wakeup[user] = Wakeup(user, new_wakeup, msg.channel.id)
        await msg.reply(
            f"Daily pings with your todo list will appear here, <@{user}>!\n"
            "`wakeup <time>` changes the time, `wakeup set` resets the channel, and "
            "`wakeup disable` shuts it up."
        )
        await msg.delete()
    else:
        data.wakeup[user] = Wakeup(
            user, new_wakeup, cast(int, data.wakeup[user].channel)
        )
        user_time = logical_time_repr(new_wakeup, data.timezones[user].tz)
        await msg.reply(f"Got it, <@{user}>, your wakeup time was set to {user_time}.")
        await msg.delete()
