from __future__ import annotations

from abc import ABC
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from core.utils.parse import Warn


class Context(ABC):
    def content(self, *args) -> str:
        return ""

    async def send(self, response: str, *args) -> None:
        ...

    async def reply(self, response: str, *args) -> None:
        ...

    async def delete(self, *args) -> None:
        ...

    async def is_timezone_set(self) -> bool:
        return False

    async def react(self, emoji: str) -> None:
        ...

    async def warn_message(self, warnings: List[Warn]) -> None:
        ...

    @property
    def user_id(self) -> int:
        return -1

    @property
    def channel_id(self) -> int:
        return -1
