from typing import List
from core.context import Context
from core.data.writable import Alert
from core.data.handler import DataHandler
from core.utils.parse_data import get_day_to_reminders, list_reminders


async def show_reminders(ctx: Context, data: DataHandler) -> None:
    reminder_str = list_reminders(data, ctx.user_id)
    if reminder_str:
        await ctx.reply(
            f"Here are your reminders, <@{ctx.user_id}>."
            + ("\n```\n" + reminder_str + "\n```")
        )
    else:
        await ctx.reply(f"You have no reminders, <@{ctx.user_id}>.")


async def delete_reminder(ctx: Context, data: DataHandler, index: int) -> None:
    shit = get_day_to_reminders(data, ctx.user_id)
    reminders: List[Alert] = [y[1] for x in shit.values() for y in x]
    if index <= 0 or index > len(reminders):
        await ctx.reply(f"Hey <@{ctx.user_id}>, you're an idiot :D")
    else:
        data.tasks.remove(reminders[index - 1])
        await ctx.reply(
            f"Hey <@{ctx.user_id}>, {reminders[index - 1].full_desc} was deleted."
        )
    await ctx.delete()
