from typing import Any

from custom_typing.protocols import Repr_able


def green(x: Repr_able, **kwargs: Any):
    print(f"\033[38;2;20;255;20m{x}\033[0m", **kwargs)


def yellow(x: Repr_able, **kwargs: Any):
    print(f"\033[38;2;255;255;20m{x}\033[0m", **kwargs)


def red(x: Repr_able, **kwargs: Any):
    print(f"\033[38;2;255;20;20m{x}\033[0m", **kwargs)
