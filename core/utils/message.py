from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING, Optional

import discord


if TYPE_CHECKING:
    from discord.message import Message


async def last_msg(channel: discord.PartialMessageable) -> Message:
    return await channel.history(limit=1).__anext__()


async def next_msg(
    channel: discord.PartialMessageable,
    user_id: int,
    is_not: Optional[Message] = None,
    sec: int = 3,
) -> Optional[Message]:
    for _ in range(sec * 2):
        await asyncio.sleep(0.5)
        if (msg := await last_msg(channel)).author.id == user_id and msg != is_not:
            return msg
    return None


async def message_deleted(
    orig_channel: discord.channel.PartialMessageable, msg: Message
) -> bool:
    try:
        await orig_channel.fetch_message(msg.id)
    except discord.NotFound:
        return True
    return False
