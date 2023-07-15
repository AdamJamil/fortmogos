from __future__ import annotations
from typing import TYPE_CHECKING, Tuple
from unittest.mock import MagicMock

from pytz import utc
from core.data.writable import Timezone, Wakeup
from core.timer import now
from core.utils.constants import fakemogus_id, testmogus_id, FAKE_TOKEN, test_channel_id
from core.utils.message import last_msg, next_msg
from datetime import time as Time, datetime as dt

if TYPE_CHECKING:
    from discord import PartialMessageable
    from discord.message import Message


def reset_data() -> None:
    now.suppose_it_is(dt.now(tz=utc).replace(tzinfo=None))
    now.set_speed(1)

    from core.bot import data

    data.alert_channels.clear()

    for attr in dir(data):
        if attr.startswith("__"):
            continue
        thing = getattr(data, attr)
        if hasattr(thing, "clear"):
            print(attr)
            thing.clear()

    data.timezones.clear()
    data.timezones[testmogus_id] = Timezone(testmogus_id, "US/Eastern")

    data.wakeup.clear()
    data.wakeup[testmogus_id] = Wakeup(testmogus_id, Time(hour=10), test_channel_id)


def mock_put(put_save: MagicMock) -> None:
    put_save.return_value = None


def mock_get_token(get_token: MagicMock) -> None:
    get_token.return_value = FAKE_TOKEN


async def query_channel(
    txt: str, channel: PartialMessageable
) -> Tuple[Message, Message]:
    query = await channel.send(txt)

    assert (
        response := await next_msg(channel, fakemogus_id, is_not=query)
    ), "Timed out waiting for response."

    return query, response


async def query_message_with_reaction(
    reaction: str, message: Message, channel: PartialMessageable
) -> Message:
    last = await last_msg(channel)
    await message.add_reaction(reaction)

    assert (
        response := await next_msg(channel, fakemogus_id, is_not=last)
    ), "Timed out waiting for response."

    return response
