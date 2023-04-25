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
    elif msg.content.startswith("in "):
        await set_in(msg, data, client)


async def set_daily(
    msg: discord.message.Message, data: DataHandler, client: discord.Client
) -> None:
    tokens = [x for x in msg.content.split(" ") if x]
    time_str, reminder_str = tokens[1], " ".join(tokens[2:])
    if isinstance((reminder_time := parse_time(time_str)), str):
        response = msg.reply(
            f"Fuck you, <@{msg.author.id}>! "
            f"Your command `{msg.content}` failed: {reminder_time}"
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
        response = msg.reply(
            f"<@{msg.author.id}>'s daily reminder {logical_dt_repr(reminder_time)}"
            f' to "{reminder_str}" has been set.'
        )
    await response
    await msg.delete()


async def set_in(
    msg: discord.message.Message, data: DataHandler, client: discord.Client
) -> None:
    tokens = [x for x in msg.content.split(" ") if x]
    duration_str, reminder_str = tokens[1], " ".join(tokens[2:])
    if isinstance((reminder_time := parse_duration(duration_str, now())), str):
        response = msg.reply(
            f"Fuck you, <@{msg.author.id}>! "
            f"Your command `{msg.content}` failed: {reminder_time}"
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
        response = msg.reply(
            f"<@{msg.author.id}>'s reminder {logical_dt_repr(reminder_time)}"
            f' to "{reminder_str}" has been set.'
        )
    await response
    await msg.delete()
