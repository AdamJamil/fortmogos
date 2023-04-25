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
        shit = list_reminders(data)
        if shit:
            await msg.reply(
                f"Here are your reminders, <@{msg.author.id}>."
                + ("\n```\n" + shit + "\n```")
            )
        else:
            await msg.reply(f"You have no reminders, <@{msg.author.id}>.")
        await msg.delete()
    elif msg.content.startswith("delete"):
        idx = int(msg.content.split(" ")[1])
        shit = get_day_to_reminders(data)
        reminders: List[Alert] = [y[1] for x in shit.values() for y in x]
        if idx <= 0 or idx > len(reminders):
            await msg.reply(f"Hey <@{msg.author.id}>, you're an idiot :D")
        else:
            data.tasks.remove(reminders[idx - 1])
            await msg.reply(f"Hey <@{msg.author.id}>, your alert was deleted.")
        await msg.delete()
