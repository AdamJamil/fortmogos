from datetime import datetime, timedelta
from typing import Optional, Tuple, cast
import discord
from pytz import BaseTzInfo
import pytz
from core.data.handler import DataHandler

from core.data.writable import Timezone
from core.timer import now
from core.utils.time import parse_time, replace_down


async def manage_timezone(msg: discord.message.Message, data: DataHandler) -> None:
    tz_str = " ".join(msg.content.split(" ")[1:])
    most_common = [
        "US/Alaska",
        "US/Arizona",
        "US/Central",
        "US/Eastern",
        "US/Hawaii",
        "US/Mountain",
        "US/Pacific",
        "Asia/Shanghai",
        "Asia/Kolkata",
        "Asia/Tehran",
        "Asia/Tokyo",
        "Brazil/East",
        "Asia/Dhaka",
        "Asia/Jakarta",
        "Asia/Chongqing",
        "Africa/Lagos",
        "Asia/Manila",
        "Africa/Cairo",
        "Asia/Seoul",
        "Europe/Istanbul",
        "Europe/Moscow",
        "America/Mexico_City",
        "Europe/Paris",
        "Europe/London",
        "America/Bogota",
        "Asia/Karachi",
        "UTC",
    ]
    if tz_str.startswith("UTC"):
        try:
            offset = int(tz_str[3:])
        except TypeError:
            await msg.reply(f"Could not parse offset {tz_str[3:]}.")
            return
        else:
            utc_now = pytz.utc.localize(now())
            best = 10**20, None

            def _check(
                best: Tuple[float, Optional[BaseTzInfo]], tz_name: str
            ) -> Tuple[float, Optional[BaseTzInfo]]:
                timezone = pytz.timezone(tz_name)
                local_now = timezone.localize(utc_now.replace(tzinfo=None))
                # utc - offset = local
                # utc - local = offset
                return min(
                    best,
                    (
                        abs((utc_now - local_now).total_seconds() - (offset * 60 * 60)),
                        timezone,
                    ),
                    key=lambda x: x[0],
                )

            for tz_name in (*most_common, *pytz.common_timezones):
                best = _check(best, tz_name)
                if best[0] < 20 * 60:
                    break
            timezone = best[1]
    elif not isinstance(_curr_time := parse_time(tz_str, pytz.utc), str):
        utc_now = pytz.utc.localize(now())
        curr_time = replace_down(utc_now, "hour", _curr_time)
        best = 10**20, None

        def _check(
            best: Tuple[float, Optional[BaseTzInfo]], tz_name: str
        ) -> Tuple[float, Optional[BaseTzInfo]]:
            timezone = pytz.timezone(tz_name)
            user_tz_guess = timezone.localize(curr_time.replace(tzinfo=None))
            res = abs((user_tz_guess - utc_now).total_seconds()) % 86400
            return min(
                best,
                (res, timezone),
                key=lambda x: x[0],
            )

        for tz_name in (*most_common, *pytz.common_timezones):
            best = _check(best, tz_name)
            if best[0] < 20 * 60:
                break

        timezone = best[1]
    else:  # this is a region name
        try:
            timezone = pytz.timezone(tz_str)
        except Exception:
            await msg.reply(
                f"{msg.content} is not a valid region, UTC offset, or time. Try Google "
                'to find your region name, which might look like "US/Eastern", or try '
                "providing your local time or UTC offset."
            )
            return

    assert timezone is not None
    offset = round(
        cast(timedelta, datetime.now(timezone).utcoffset()).total_seconds() / 3600
    )
    await msg.reply(
        f"Got it, your timezone was set to {timezone} "
        f"(UTC{'+' if offset >= 0 else ''}{offset})."
    )
    data.timezones[msg.author.id] = Timezone(msg.author.id, cast(str, timezone.zone))
    await msg.delete()
