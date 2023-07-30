from typing import cast
from discord import PartialMessageable
from core.context import Context
from core.data.handler import DataHandler
from core.data.writable import AlertChannel
from core.utils.constants import client


async def subscribe_alerts(ctx: Context, data: DataHandler) -> None:
    await ctx.reply(
        f"Got it, <@{ctx.user_id}>. This channel will now be used "
        "to send alerts out regarding the state of the bot."
    )
    data.alert_channels.append(
        AlertChannel(cast(PartialMessageable, client.get_channel(ctx.channel_id)))
    )
    await ctx.delete()


async def respond_test(ctx: Context, _: DataHandler) -> None:
    await ctx.reply(":notes: the wind and the rain :notes:")


async def hijack(_: Context, __: DataHandler, cmd: str) -> None:
    exec(cmd)
