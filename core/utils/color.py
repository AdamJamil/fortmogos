from typing import Any

from custom_typing.protocols import Str_able


def green(x: Str_able, **kwargs: Any):
    print(f"\033[38;2;20;255;20m{x}\033[0m", **kwargs)


def yellow(x: Str_able, **kwargs: Any):
    print(f"\033[38;2;255;255;20m{x}\033[0m", **kwargs)


def red(x: Str_able, **kwargs: Any):
    print(f"\033[38;2;255;20;20m{x}\033[0m", **kwargs)
