from typing import Any


def green(x: str, **kwargs: Any):
    print(f"\033[38;2;20;255;20m{x}\033[0m", **kwargs)


def yellow(x: str, **kwargs: Any):
    print(f"\033[38;2;255;255;20m{x}\033[0m", **kwargs)


def red(x: str, **kwargs: Any):
    print(f"\033[38;2;255;20;20m{x}\033[0m", **kwargs)
