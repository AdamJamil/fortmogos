import discord
from core.alert import DailyAlert, SingleAlert
from core.data import PersistentInfo
from core.timer import now

from core.utils import logical_dt_repr, parse_duration, parse_time


async def set_reminder(
    msg: discord.message.Message, data: PersistentInfo, client: discord.Client
) -> None:
    if msg.content.startswith("daily "):
        tokens = [x for x in msg.content.split(" ") if x]
        time_str, reminder_str = tokens[1], " ".join(tokens[2:])
        if isinstance((reminder_time := parse_time(time_str)), str):
            response = msg.reply(
                f"Fuck you, <@{msg.author.id}>! "
                f"Your command `{msg.content}` failed: {reminder_time}"
            )
        else:
            data.tasks.append(
                DailyAlert(
                    reminder_str, msg.author.id, msg.channel.id, client, reminder_time
                )
            )
            response = msg.reply(
                f'<@{msg.author.id}>\'s daily reminder {logical_dt_repr(reminder_time)}'
                f' to "{reminder_str}" has been set.'
            )
        await response
        await msg.delete()
    elif msg.content.startswith("in "):
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
                    reminder_str, msg.author.id, msg.channel.id, client, reminder_time
                )
            )
            response = msg.reply(
                f'<@{msg.author.id}>\'s reminder {logical_dt_repr(reminder_time)}'
                f' to "{reminder_str}" has been set.'
            )
        await response
        await msg.delete()
