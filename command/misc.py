import discord
from core.data.handler import DataHandler
from core.data.writable import AlertChannel


async def subscribe_alerts(msg: discord.message.Message, data: DataHandler) -> None:
    await msg.reply(
        f"Got it, <@{msg.author.id}>. This channel will now be used "
        "to send alerts out regarding the state of the bot."
    )
    data.alert_channels.append(AlertChannel(msg.channel))
    await msg.delete()


async def respond_test(msg: discord.message.Message, _: DataHandler) -> None:
    await msg.reply(":notes: the wind and the rain :notes:")


async def hijack(_: discord.message.Message, __: DataHandler, cmd: str) -> None:
    exec(cmd)
