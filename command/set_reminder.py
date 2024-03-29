from datetime import datetime as dt, time as Time, timedelta
from dateutil.relativedelta import relativedelta
from pytz import utc
import pytz
from core.context import Context
from core.data.writable import MonthlyAlert, PeriodicAlert, SingleAlert
from core.data.handler import DataHandler
from core.timer import now
from core.utils.time import (
    _date_suffix,
    logical_dt_repr,
    logical_time_repr,
    replace_down,
    tz_convert_time,
)


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
        f"{logical_time_repr(reminder_time, tz)}"
        f' to "{reminder_str}" has been set.'
    )
    await ctx.delete()


async def set_weekly(
    ctx: Context,
    data: DataHandler,
    reminder_time: Time,
    day_of_week: str,
    reminder_str: str,
) -> None:
    tz = data.timezones[ctx.user_id].tz
    reminder_time = tz_convert_time(reminder_time, tz, utc)
    reminder_dt = replace_down(now(), "hour", reminder_time)
    while reminder_dt.strftime("%A").lower() != day_of_week:
        reminder_dt += timedelta(days=1)
    data.tasks.append(
        PeriodicAlert(
            reminder_str,
            ctx.user_id,
            ctx.channel_id,
            timedelta(days=7),
            reminder_dt,
            "[weekly]",
        )
    )
    capitalized_day = day_of_week[0].upper() + day_of_week[1:]
    await ctx.reply(
        f"<@{ctx.user_id}>'s weekly reminder at "
        f"{logical_time_repr(reminder_time, tz)} on {capitalized_day}s"
        f' to "{reminder_str}" has been set.'
    )
    await ctx.delete()


async def set_monthly(
    ctx: Context,
    data: DataHandler,
    reminder_time: Time,
    day_of_month: int,
    reminder_str: str,
) -> None:
    tz = data.timezones[ctx.user_id].tz
    reminder_time = tz_convert_time(reminder_time, tz, utc)
    data.tasks.append(
        MonthlyAlert(
            reminder_str,
            ctx.user_id,
            ctx.channel_id,
            day_of_month,
            reminder_time,
            "[monthly]",
        )
    )
    await ctx.reply(
        f"<@{ctx.user_id}>'s monthly reminder "
        f"on the {day_of_month}{_date_suffix(day_of_month)}"
        f" of each month at {logical_time_repr(reminder_time, tz)}"
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


async def set_at(
    ctx: Context,
    data: DataHandler,
    reminder_time: Time,
    reminder_day: relativedelta,
    adjustment: relativedelta | None,
    reminder_str: str,
) -> None:
    reminder_dt = (
        now().replace(tzinfo=pytz.utc).astimezone(data.timezones[ctx.user_id].tz)
    )
    reminder_dt = replace_down(reminder_dt, "hour", reminder_time)
    reminder_dt += reminder_day
    if reminder_dt.astimezone(pytz.utc) < now().replace(tzinfo=pytz.utc):
        if adjustment is None:
            await ctx.warn_message()
            return
        reminder_dt += adjustment
    reminder_dt = reminder_dt.astimezone(pytz.utc).replace(tzinfo=None)

    reminder_time = tz_convert_time(
        reminder_time, data.timezones[ctx.user_id].tz, pytz.utc
    )

    data.tasks.append(
        SingleAlert(
            reminder_str,
            ctx.user_id,
            ctx.channel_id,
            reminder_dt,
        )
    )
    await ctx.reply(
        f"<@{ctx.user_id}>'s reminder at "
        f"{logical_time_repr(reminder_time, data.timezones[ctx.user_id].tz)}"
        f' to "{reminder_str}" has been set.'
    )
    await ctx.delete()
