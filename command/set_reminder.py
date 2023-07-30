from datetime import datetime as dt, time as Time, timedelta
from pytz import utc
from core.context import Context
from core.data.writable import PeriodicAlert, SingleAlert
from core.data.handler import DataHandler
from core.timer import now
from core.utils.time import logical_dt_repr, replace_down, tz_convert_time


async def set_daily(
    ctx: Context,
    data: DataHandler,
    reminder_time: Time,
    reminder_str: str,
) -> None:
    tz = data.timezones[ctx.user_id].tz
    reminder_time = tz_convert_time(reminder_time, tz, utc)
    reminder_dt = replace_down((curr := now()), "hour", reminder_time)
    if reminder_dt < curr:
        reminder_dt += timedelta(days=1)
    data.tasks.append(
        PeriodicAlert(
            reminder_str,
            ctx.user_id,
            ctx.channel_id,
            timedelta(days=1),
            reminder_dt,
            "[daily]",
        )
    )
    await ctx.reply(
        f"<@{ctx.user_id}>'s daily reminder at "
        f"{logical_dt_repr(reminder_time, tz)}"
        f' to "{reminder_str}" has been set.'
    )
    await ctx.delete()


async def set_in(
    ctx: Context,
    data: DataHandler,
    reminder_time: dt,
    reminder_str: str,
) -> None:
    data.tasks.append(
        SingleAlert(
            reminder_str,
            ctx.user_id,
            ctx.channel_id,
            reminder_time,
        )
    )
    await ctx.reply(
        f"<@{ctx.user_id}>'s reminder "
        f"{logical_dt_repr(reminder_time, data.timezones[ctx.user_id].tz)}"
        f' to "{reminder_str}" has been set.'
    )
    await ctx.delete()
