from abc import ABC
from typing import Any, List, Union

from discord import Member, Message, Reaction, User
from core.context import Context
from core.utils.parse import Warn
from core.utils.constants import warning_emoji


class DiscordContext(Context, ABC):
    message: Message
    _user_id: int

    async def send(self, response: str, *_) -> None:
        await self.message.channel.send(response)

    async def reply(self, response: str, *_) -> None:
        await self.message.reply(response)

    async def delete(self, *_) -> None:
        await self.message.delete()

    async def is_timezone_set(self) -> bool:
        from core.start import data

        return self.user_id in data.timezones

    async def react(self, emoji: str) -> None:
        await self.message.add_reaction(emoji)

    async def warn_message(self, warnings: List[Warn]) -> None:
        await self.react(warning_emoji)

    @property
    def user_id(self) -> int:
        # TODO: user ids should be platform aware
        return self._user_id

    @property
    def channel_id(self) -> int:
        # TODO: channel ids should be platform aware
        return self.message.channel.id


class DiscordMessageContext(DiscordContext):
    def __init__(self, message: Message) -> None:
        self.message = message
        self._user_id = message.author.id

    def content(self, *_: Any) -> str:
        return self.message.content

    def __repr__(self) -> str:
        return f"DiscordMessageContext from user {self.user_id}: {self.content()}"


class DiscordReactionContext(DiscordContext):
    def __init__(self, reaction: Reaction, user: Union[Member, User]) -> None:
        self.reaction = reaction
        self.message = reaction.message
        self._user_id = user.id

    def content(self, *_) -> str:
        return str(self.reaction.emoji)
