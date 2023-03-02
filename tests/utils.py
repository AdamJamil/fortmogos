from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, Tuple
from unittest.mock import MagicMock


from core.utils.message import next_msg
from core.data import PersistentInfo


if TYPE_CHECKING:
    from discord import PartialMessageable
    from discord.message import Message


def dict_subset(x: Dict[Any, Any], y: Dict[Any, Any]):
    return all(y[k] == v for k, v in x.items())


def reset_data() -> None:
    from core.bot import data

    data.tasks = []
    data.alert_channels = []


def mock_data(pickle_load: MagicMock) -> None:
    pickle_load.return_value = PersistentInfo.__new__(PersistentInfo)
    pickle_load.return_value.tasks = []
    pickle_load.return_value.alert_channels = []


async def query_channel(
    txt: str, channel: PartialMessageable
) -> Tuple[Message, Message]:
    query = await channel.send(txt)

    assert (
        response := await next_msg(channel, 1061719682773688391, is_not=query)
    ), "Timed out waiting for response."

    return query, response
