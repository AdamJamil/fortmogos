from datetime import datetime, timedelta
from typing import cast
import discord
from pytz import BaseTzInfo
from core.data.handler import DataHandler

from core.data.writable import Timezone


async def manage_timezone(
    msg: discord.message.Message, data: DataHandler, timezone: BaseTzInfo
) -> None:
    offset = round(
        cast(timedelta, datetime.now(timezone).utcoffset()).total_seconds() / 3600
    )
    await msg.reply(
        f"Got it, your timezone was set to {timezone} "
        f"(UTC{'+' if offset >= 0 else ''}{offset})."
    )
    data.timezones[msg.author.id] = Timezone(msg.author.id, cast(str, timezone.zone))
    await msg.delete()
