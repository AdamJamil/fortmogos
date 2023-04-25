from typing import Any, Protocol


class Color(Protocol):
    def __call__(self, x: str, **kwargs: Any) -> None:
        ...


class Measureable(Protocol):
    def __len__(self) -> int:
        ...


class Str_able(Protocol):
    def __str__(self) -> str:
        ...
