from __future__ import annotations
import queue
from typing import TYPE_CHECKING, Tuple
from unittest.mock import MagicMock
from core.utils.constants import fakemogus_id, FAKE_TOKEN


from core.utils.message import next_msg
from core.data import PersistentInfo


if TYPE_CHECKING:
    from discord import PartialMessageable
    from discord.message import Message


def reset_data() -> None:
    from core.bot import data

    data.clear_tasks()
    data.alert_channels.clear()


def mock_load(pickle_load: MagicMock) -> None:
    pickle_load.return_value = PersistentInfo.__new__(PersistentInfo)
    pickle_load.return_value.message_queue = queue.Queue[bool]()
    pickle_load.return_value._tasks = []
    pickle_load.return_value.alert_channels = []


def mock_save(data_save: MagicMock) -> None:
    data_save.return_value = None


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
