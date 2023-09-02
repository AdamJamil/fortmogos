from core.context import Context
from core.data.handler import DataHandler


async def respond_test(ctx: Context, _: DataHandler) -> None:
    await ctx.reply(":notes: the wind and the rain :notes:")


async def hijack(ctx: Context, __: DataHandler, cmd: str) -> None:
    await ctx.reply("fuck off :D")
