from typing import List
import discord
from core.data.writable import Alert
from core.data.handler import DataHandler
from core.utils.parse_data import get_day_to_reminders, list_reminders


async def manage_reminder(msg: discord.message.Message, data: DataHandler) -> None:
    if msg.content in [
        "list reminders",
        "show reminders",
        "see reminders",
        "view reminders",
    ]:
        shit = list_reminders(data, msg.author.id)
        if shit:
            await msg.reply(
                f"Here are your reminders, <@{msg.author.id}>."
                + ("\n```\n" + shit + "\n```")
            )
        else:
            await msg.reply(f"You have no reminders, <@{msg.author.id}>.")
    elif msg.content.startswith("delete reminder ") or msg.content.startswith(
        "remove reminder "
    ):
        idx = int(msg.content.split(" ")[2])
        shit = get_day_to_reminders(data, msg.author.id)
        reminders: List[Alert] = [y[1] for x in shit.values() for y in x]
        if idx <= 0 or idx > len(reminders):
            await msg.reply(f"Hey <@{msg.author.id}>, you're an idiot :D")
        else:
            data.tasks.remove(reminders[idx - 1])
            await msg.reply(
                f"Hey <@{msg.author.id}>, {reminders[idx - 1].full_desc} was deleted."
            )
    await msg.delete()
