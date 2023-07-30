from datetime import datetime, timedelta
from typing import cast
from pytz import BaseTzInfo
from core.context import Context
from core.data.handler import DataHandler

from core.data.writable import Timezone


async def manage_timezone(
    ctx: Context, data: DataHandler, timezone: BaseTzInfo
) -> None:
    offset = round(
        cast(timedelta, datetime.now(timezone).utcoffset()).total_seconds() / 3600
    )
    await ctx.reply(
        f"Got it, your timezone was set to {timezone} "
        f"(UTC{'+' if offset >= 0 else ''}{offset})."
    )
    data.timezones[ctx.user_id] = Timezone(ctx.user_id, cast(str, timezone.zone))
    await ctx.delete()
