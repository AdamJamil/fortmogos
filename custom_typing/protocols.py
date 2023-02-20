from typing import Any, Protocol


class Color(Protocol):
    def __call__(self, x: str, **kwargs: Any) -> None:
        ...
