from datetime import timedelta
import discord
from core.data.writable import PeriodicAlert, SingleAlert
from core.data.handler import DataHandler
from core.timer import now
from core.utils.time import logical_dt_repr, parse_duration, parse_time, replace_down


async def set_reminder(
    msg: discord.message.Message, data: DataHandler, client: discord.Client
) -> None:
    if msg.content.startswith("daily "):
        await set_daily(msg, data, client)
    if msg.content.startswith("weekly "):
        await set_weekly(msg, data, client)
    elif msg.content.startswith("in "):
        await set_in(msg, data, client)


async def set_daily(
    msg: discord.message.Message, data: DataHandler, client: discord.Client
) -> None:
    tokens = [x for x in msg.content.split(" ") if x]
    time_str, reminder_str = tokens[1], " ".join(tokens[2:])
    tz = data.timezones[msg.author.id].tz
    if isinstance((reminder_time := parse_time(time_str, tz)), str):
        await msg.reply(
            f"Fuck you, <@{msg.author.id}>! " f"Your command failed: {reminder_time}"
        )
    else:
        reminder_dt = replace_down((curr := now()), "hour", reminder_time)
        if reminder_dt < curr:
            reminder_dt += timedelta(days=1)
        data.tasks.append(
            PeriodicAlert(
                reminder_str,
                msg.author.id,
                msg.channel.id,
                timedelta(days=1),
                reminder_dt,
                "[daily]",
            )
        )
        await msg.reply(
            f"<@{msg.author.id}>'s daily reminder at "
            f"{logical_dt_repr(reminder_time, tz)}"
            f' to "{reminder_str}" has been set.'
        )
        await msg.delete()


async def set_weekly(
    msg: discord.message.Message, data: DataHandler, client: discord.Client
) -> None:
    tokens = [x for x in msg.content.split(" ") if x]
    day_str, time_str, reminder_str = tokens[1].lower(), tokens[2], " ".join(tokens[3:])
    days = [
        "sunday",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
    ]
    tz = data.timezones[msg.author.id].tz
    if isinstance((reminder_time := parse_time(time_str, tz)), str):
        await msg.reply(
            f"Fuck you, <@{msg.author.id}>! Your command failed: {reminder_time}"
        )
    elif day_str not in days:
        await msg.reply(
            f"Fuck you, <@{msg.author.id}>! "
            f"Your command failed: {day_str} is not a day."
        )
    else:
        reminder_dt = replace_down(now(), "hour", reminder_time)
        while int(reminder_dt.strftime("%w")) != days.index(day_str):
            reminder_dt += timedelta(days=1)
        data.tasks.append(
            PeriodicAlert(
                reminder_str,
                msg.author.id,
                msg.channel.id,
                timedelta(days=7),
                reminder_dt,
                "[weekly]",
            )
        )
        day_str = day_str[0].upper() + day_str[1:] + "s"
        await msg.reply(
            f"<@{msg.author.id}>'s weekly reminder at "
            f"{logical_dt_repr(reminder_time, tz)} on {day_str}"
            f' to "{reminder_str}" has been set.\n'
            f"First reminder: {reminder_dt} (UTC+0)."
        )
        await msg.delete()


async def set_in(
    msg: discord.message.Message, data: DataHandler, client: discord.Client
) -> None:
    tokens = [x for x in msg.content.split(" ") if x]
    duration_str, reminder_str = tokens[1], " ".join(tokens[2:])
    if isinstance(
        (reminder_time := parse_duration(duration_str, now())),
        str,
    ):
        await msg.reply(
            f"Fuck you, <@{msg.author.id}>! " f"Your command failed: {reminder_time}"
        )
    else:
        data.tasks.append(
            SingleAlert(
                reminder_str,
                msg.author.id,
                msg.channel.id,
                reminder_time,
            )
        )
        await msg.reply(
            f"<@{msg.author.id}>'s reminder "
            f"{logical_dt_repr(reminder_time, data.timezones[msg.author.id].tz)}"
            f' to "{reminder_str}" has been set.'
        )
        await msg.delete()
