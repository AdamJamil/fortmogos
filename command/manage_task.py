from typing import cast
from core.context import Context
from core.data.writable import UserTask
from core.data.handler import DataHandler


async def add_task(ctx: Context, data: DataHandler, desc: str) -> None:
    data.user_tasks.append(UserTask(ctx.user_id, desc))
    await ctx.reply(
        f"Your task to `{desc}` was added to your list. Try `see tasks` to view it."
    )
    await ctx.delete()


async def show_tasks(ctx: Context, data: DataHandler) -> None:
    res = "\n".join(
        f"{i+1}) {cast(str, y.desc)}"
        for i, y in enumerate(
            x for x in data.user_tasks if cast(int, x.user_id) == ctx.user_id
        )
    )
    await ctx.reply(
        f"Here is your todo list, <@{ctx.user_id}>:\n```\n{res}\n```"
        if res
        else "Your todo list is empty."
    )
    await ctx.delete()


async def delete_task(ctx: Context, data: DataHandler, index: int) -> None:
    user_tasks = [x for x in data.user_tasks if cast(int, x.user_id) == ctx.user_id]
    if index <= 0 or index > len(user_tasks):
        await ctx.reply(f"Hey <@{ctx.user_id}>, you're an idiot :D")
    else:
        data.user_tasks.remove(user_tasks[index - 1])
        await ctx.reply(
            f"Hey <@{ctx.user_id}>, your task "
            f"`{user_tasks[index - 1].desc}` was deleted."
        )
    await ctx.delete()
