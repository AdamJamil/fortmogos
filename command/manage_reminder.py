from typing import List
import discord
from core.data.writable import Alert
from core.data.handler import DataHandler
from core.utils.parse_data import get_day_to_reminders, list_reminders


async def show_reminders(msg: discord.message.Message, data: DataHandler) -> None:
    reminder_str = list_reminders(data, msg.author.id)
    if reminder_str:
        await msg.reply(
            f"Here are your reminders, <@{msg.author.id}>."
            + ("\n```\n" + reminder_str + "\n```")
        )
    else:
        await msg.reply(f"You have no reminders, <@{msg.author.id}>.")


async def delete_reminder(
    msg: discord.message.Message, data: DataHandler, index: int
) -> None:
    shit = get_day_to_reminders(data, msg.author.id)
    reminders: List[Alert] = [y[1] for x in shit.values() for y in x]
    if index <= 0 or index > len(reminders):
        await msg.reply(f"Hey <@{msg.author.id}>, you're an idiot :D")
    else:
        data.tasks.remove(reminders[index - 1])
        await msg.reply(
            f"Hey <@{msg.author.id}>, {reminders[index - 1].full_desc} was deleted."
        )
    await msg.delete()
