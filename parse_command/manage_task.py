from typing import cast
import discord
from core.data.writable import UserTask
from core.data.handler import DataHandler


async def add_task(msg: discord.message.Message, data: DataHandler) -> None:
    desc = " ".join(msg.content.split(" ")[1:])
    data.user_tasks.append(UserTask(msg.author.id, desc))
    await msg.reply(
        f"Your task to `{desc}` was added to your list. Try `see tasks` to view it."
    )
    await msg.delete()


async def show_tasks(msg: discord.message.Message, data: DataHandler) -> None:
    res = "\n".join(
        f"{i+1}) {cast(str, y.desc)}"
        for i, y in enumerate(
            x for x in data.user_tasks if cast(int, x.user_id) == msg.author.id
        )
    )
    await msg.reply(
        f"Here is your todo list, <@{msg.author.id}>:\n```\n{res}\n```"
        if res
        else "Your todo list is empty."
    )
    await msg.delete()


async def delete_task(msg: discord.message.Message, data: DataHandler) -> None:
    idx = int(msg.content.split(" ")[2])
    user_tasks = [x for x in data.user_tasks if cast(int, x.user_id) == msg.author.id]
    if idx <= 0 or idx > len(user_tasks):
        await msg.reply(f"Hey <@{msg.author.id}>, you're an idiot :D")
    else:
        data.user_tasks.remove(user_tasks[idx - 1])
        await msg.reply(f"Hey <@{msg.author.id}>, your task was deleted.")
    await msg.delete()
