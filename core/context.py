from __future__ import annotations

from abc import ABC


class Context(ABC):
    def content(self) -> str:
        return ""

    async def send(self, response: str) -> None:
        ...

    async def reply(self, response: str) -> None:
        ...

    async def delete(self) -> None:
        ...

    async def is_timezone_set(self) -> bool:
        return False

    async def react(self, emoji: str) -> None:
        ...

    async def warn_message(self) -> None:
        ...

    @property
    def user_id(self) -> int:
        return -1

    @property
    def channel_id(self) -> int:
        return -1
