from __future__ import annotations

from typing import cast
from datetime import time as Time
import pytz
from pytz import utc
from core.context import Context

from core.data.handler import DataHandler
from core.data.writable import Wakeup
from core.utils.time import logical_time_repr, tz_convert_time


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


async def init_wakeup(ctx: Context, data: DataHandler) -> None:
    await ctx.send(
        f"Daily pings with your todo list will appear here, <@{ctx.user_id}>!\n"
        "`wakeup <time>` changes the time, `wakeup set` resets the channel, and "
        "`wakeup disable` shuts it up.",
    )
    data.wakeup[ctx.user_id] = Wakeup(
        ctx.user_id,
        default_wakeup(ctx.user_id, data),
        ctx.channel_id,
    )


async def enable(ctx: Context, data: DataHandler) -> None:
    user = ctx.user_id
    if user not in data.wakeup:
        data.wakeup[user] = Wakeup(user, default_wakeup(user, data), ctx.channel_id)
        await ctx.reply(
            f"Daily pings with your todo list will appear here, <@{user}>!\n"
            "`wakeup <time>` changes the time, `wakeup set` resets the channel, and "
            "`wakeup disable` shuts it up."
        )
    elif cast(bool, data.wakeup[user].disabled):
        await ctx.reply("Re-enabled your daily todo reminders.")
    else:
        await ctx.reply("Already enabled, galaxy brain.")
    await ctx.delete()


async def disable(ctx: Context, data: DataHandler) -> None:
    user = ctx.user_id
    if user not in data.wakeup:
        data.wakeup[user] = Wakeup(
            user,
            default_wakeup(user, data),
            ctx.channel_id,
            disabled=True,
        )
        await ctx.reply(
            "You don't have a wakeup set. Setting and disabling one. "
            "You can undo this with `wakeup enable`."
        )
        await ctx.delete()
    elif cast(bool, data.wakeup[user].disabled):
        await ctx.reply("It's already disabled, galaxy brain.")
        await ctx.delete()
    else:
        await ctx.reply(
            f"Got it, <@{user}>, you will no longer "
            "receive daily todo reminders. You can undo this with `wakeup enable`."
        )
        await ctx.delete()
        data.wakeup[user] = Wakeup(
            user,
            data.wakeup[user].time,
            cast(int, data.wakeup[user].channel),
            disabled=True,
        )


async def set_channel(ctx: Context, data: DataHandler) -> None:
    user = ctx.user_id
    if user not in data.wakeup:
        data.wakeup[user] = Wakeup(user, default_wakeup(user, data), ctx.channel_id)
        await ctx.reply(
            f"Daily pings with your todo list will appear here, <@{user}>!\n"
            "`wakeup <time>` changes the time, `wakeup set` resets the channel, and "
            "`wakeup disable` shuts it up."
        )
        await ctx.delete()
    else:
        await ctx.reply(
            f"Got it, <@{user}>, your daily todo list will appear here now."
        )
        await ctx.delete()


async def change_wakeup_time(
    ctx: Context,
    data: DataHandler,
    new_wakeup: Time,
) -> None:
    tz = data.timezones[ctx.user_id].tz
    new_wakeup = tz_convert_time(new_wakeup, tz, utc)
    user = ctx.user_id
    if user not in data.wakeup:
        data.wakeup[user] = Wakeup(user, new_wakeup, ctx.user_id)
        await ctx.reply(
            f"Daily pings with your todo list will appear here, <@{user}>!\n"
            "`wakeup <time>` changes the time, `wakeup set` resets the channel, and "
            "`wakeup disable` shuts it up."
        )
        await ctx.delete()
    else:
        data.wakeup[user] = Wakeup(
            user, new_wakeup, cast(int, data.wakeup[user].channel)
        )
        user_time = logical_time_repr(new_wakeup, data.timezones[user].tz)
        await ctx.reply(f"Got it, <@{user}>, your wakeup time was set to {user_time}.")
        await ctx.delete()
