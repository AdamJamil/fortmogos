from __future__ import annotations
import asyncio
from typing import List, Literal, Tuple, Union, overload
from unittest.mock import MagicMock

from disc.receive import on_message, on_reaction_add
from core.data.writable import Timezone, Wakeup
from core.timer import now
from core.utils.constants import fakemogus_id, testmogus_id, FAKE_TOKEN
from datetime import time as Time, datetime as dt

from core.utils.time import replace_down


test_channel_id = 2394823904


def reset_data() -> None:
    now.suppose_it_is(
        dt(
            hour=0, minute=0, second=0, microsecond=0, day=2, month=9, year=2020
        ).replace(tzinfo=None)
    )
    now.set_speed(1)

    from core.start import data

    for attr in dir(data):
        if attr.startswith("__"):
            continue
        thing = getattr(data, attr)
        if hasattr(thing, "clear"):
            thing.clear()

    data.timezones.clear()
    data.timezones[testmogus_id] = Timezone(testmogus_id, "US/Eastern")

    data.wakeup.clear()
    data.wakeup[testmogus_id] = Wakeup(testmogus_id, Time(hour=10), test_channel_id)


def mock_put(put_save: MagicMock) -> None:
    put_save.return_value = None


def mock_get_token(get_token: MagicMock) -> None:
    get_token.return_value = FAKE_TOKEN


@overload
async def query_message_with_reaction(
    reaction: str, message: MockMessage, expected_messages: Literal[0]
) -> None:
    ...


@overload
async def query_message_with_reaction(
    reaction: str, message: MockMessage, expected_messages: Literal[1]
) -> MockMessage:
    ...


@overload
async def query_message_with_reaction(
    reaction: str, message: MockMessage, expected_messages: Literal[2]
) -> Tuple[MockMessage, MockMessage]:
    ...


async def query_message_with_reaction(
    reaction: str, message: MockMessage, expected_messages: int = -1
) -> Union[Tuple[MockMessage, ...], MockMessage, None]:
    initial_msgs = set(messages)

    await message.add_reaction(reaction, user=user_user)

    responses = [x for x in messages if x not in initial_msgs]

    if expected_messages >= 0:
        if len(responses) != expected_messages:
            raise AssertionError(
                f"Got {len(responses)} instead of expected {expected_messages}. "
                "Received responses:\n\t"
                + "\n\t".join(response.content for response in responses)
            )

        if expected_messages == 1:
            return responses[0]
        if expected_messages == 2:
            return responses[0], responses[1]
        raise AssertionError("Fuck you.")

    return tuple(responses)


messages: List[MockMessage] = []


class MockUser:
    def __init__(self, _id: int) -> None:
        self.id = _id


bot_user = MockUser(fakemogus_id)
user_user = MockUser(testmogus_id)


class MockChannel:
    def __init__(self, _id: int) -> None:
        self.id = _id

    async def send(self, msg: str) -> MockMessage:
        return await bot_says(msg)


test_channel = MockChannel(test_channel_id)


class MockReaction:
    def __init__(self, emoji: str, user: MockUser, message: MockMessage) -> None:
        self.emoji = emoji
        self.user = user
        self.message = message


class MockMessage:
    def __init__(self, content: str, author: MockUser) -> None:
        self.content = content
        self.author = author
        self.channel = test_channel
        self.replies: List[str] = []
        self.reactions: List[MockReaction] = []

    async def reply(self, content: str) -> None:
        self.replies.append(content)
        messages.append(MockMessage(content, bot_user))

    async def delete(self) -> None:
        messages.remove(self)

    async def add_reaction(self, emoji: str, user: MockUser = bot_user) -> None:
        self.reactions.append(MockReaction(emoji, user, self))
        await on_reaction_add(self.reactions[-1], user)  # type: ignore

    def __repr__(self) -> str:
        res = f'MockMessage(content="{self.content}", author={self.author}'
        if self.replies:
            res += f", replies={self.replies}"
        if self.reactions:
            res += f", reactions={self.reactions}"
        return res + ")"


async def _someone_says(msg: MockMessage) -> None:
    messages.append(msg)
    await on_message(msg)  # type: ignore


@overload
async def user_says(msg: str, expected_responses: Literal[0]) -> None:
    ...


@overload
async def user_says(msg: str, expected_responses: Literal[1]) -> MockMessage:
    ...


@overload
async def user_says(
    msg: str, expected_responses: Literal[2]
) -> Tuple[MockMessage, MockMessage]:
    ...


@overload
async def user_says(
    msg: str,
    expected_responses: int = -1,
) -> Union[Tuple[MockMessage, ...], MockMessage, None]:
    ...


async def user_says(
    msg: str, expected_responses: int = -1
) -> Union[Tuple[MockMessage, ...], MockMessage, None]:
    user_msg = MockMessage(msg, user_user)
    initial_msgs = set(messages)

    await _someone_says(user_msg)
    await asyncio.sleep(0.01)

    responses = [x for x in messages if x not in initial_msgs and x != user_msg]

    if expected_responses >= 0:
        if len(responses) != expected_responses:
            raise AssertionError(
                f"Got {len(responses)} instead of expected {expected_responses}. "
                "Received responses:\n\t"
                + "\n\t".join(response.content for response in responses)
            )

        if expected_responses == 1:
            return responses[0]
        if expected_responses == 2:
            return responses[0], responses[1]
        raise AssertionError("Fuck you.")

    return tuple(responses)


async def bot_says(msg: str) -> MockMessage:
    bot_msg = MockMessage(msg, bot_user)

    await _someone_says(bot_msg)

    return bot_msg


def test_message_deleted(content: str) -> bool:
    return not any(message.content == content for message in messages)


@overload
async def get_messages_at_time(
    _moment: Union[Time, dt], expected_messages: Literal[0]
) -> None:
    ...


@overload
async def get_messages_at_time(
    _moment: Union[Time, dt], expected_messages: Literal[1]
) -> MockMessage:
    ...


@overload
async def get_messages_at_time(
    _moment: Union[Time, dt], expected_messages: Literal[2]
) -> Tuple[MockMessage, MockMessage]:
    ...


@overload
async def get_messages_at_time(
    _moment: Union[Time, dt],
    expected_messages: int = -1,
) -> Union[Tuple[MockMessage, ...], MockMessage, None]:
    ...


async def get_messages_at_time(
    _moment: Union[Time, dt], expected_messages: int = -1
) -> Union[Tuple[MockMessage, ...], MockMessage, None]:
    moment = (
        replace_down(now(), "hour", _moment) if isinstance(_moment, Time) else _moment
    )

    initial_msgs = set(messages)
    now.suppose_it_is(moment)
    await asyncio.sleep(0.011)

    responses = [x for x in messages if x not in initial_msgs]

    if expected_messages >= 0:
        if len(responses) != expected_messages:
            raise AssertionError(
                f"Got {len(responses)} instead of expected {expected_messages}. "
                "Received responses:\n\t"
                + "\n\t".join(response.content for response in responses)
            )

        if expected_messages == 0:
            return None
        if expected_messages == 1:
            return responses[0]
        if expected_messages == 2:
            return responses[0], responses[1]
        raise AssertionError("Fuck you.")

    return tuple(responses)
