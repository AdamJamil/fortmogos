from typing import cast
import discord
from core.data.writable import UserTask
from core.data.handler import DataHandler


async def add_task(msg: discord.message.Message, data: DataHandler, desc: str) -> None:
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


async def delete_task(
    msg: discord.message.Message, data: DataHandler, index: int
) -> None:
    user_tasks = [x for x in data.user_tasks if cast(int, x.user_id) == msg.author.id]
    if index <= 0 or index > len(user_tasks):
        await msg.reply(f"Hey <@{msg.author.id}>, you're an idiot :D")
    else:
        data.user_tasks.remove(user_tasks[index - 1])
        await msg.reply(
            f"Hey <@{msg.author.id}>, your task "
            f"`{user_tasks[index - 1].desc}` was deleted."
        )
    await msg.delete()
