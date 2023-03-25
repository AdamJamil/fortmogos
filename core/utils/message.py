from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING, Optional

import discord
from pprint import pprint


if TYPE_CHECKING:
    from discord.message import Message


async def next_msg(
    channel: discord.PartialMessageable,
    user_id: int,
    is_not: Optional[Message] = None,
    sec: int = 3,
) -> Optional[Message]:

    print("USER_ID: " + str(user_id))

    for _ in range(sec * 2):
        await asyncio.sleep(0.5)
        if (
            msg := await channel.history(limit=1).__anext__()
        ).author.id == user_id and msg != is_not:
            return msg
        else:
            pprint(msg)
            print(msg.author.id)
    return None


async def message_deleted(
    orig_channel: discord.channel.PartialMessageable, msg: Message
) -> bool:
    try:
        await orig_channel.fetch_message(msg.id)
    except discord.NotFound:
        return True
    return False
