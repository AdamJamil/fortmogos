from __future__ import annotations
from typing import TYPE_CHECKING, Tuple
from unittest.mock import MagicMock
from core.utils.constants import fakemogus_id, FAKE_TOKEN


from core.utils.message import next_msg


if TYPE_CHECKING:
    from discord import PartialMessageable
    from discord.message import Message


def reset_data() -> None:
    from core.bot import data

    data.tasks.clear()
    data.alert_channels.clear()
    data.user_tasks.clear()


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
