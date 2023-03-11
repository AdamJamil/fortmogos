from __future__ import annotations
import difflib

import importlib
import asyncio
import inspect
import os
import traceback
from typing import Any, Dict, List
from datetime import datetime as dt
from unittest.mock import MagicMock, patch


from core.utils.constants import TEST_TOKEN, get_test_channel, test_client, sep
from tests.utils import mock_data, query_channel, reset_data
from core.bot import start as start_bot
from core.timer import now
from core.utils.color import green, red, yellow
from custom_typing.protocols import Color, Measureable


def load_test_classes() -> List[type]:
    test_classes: List[type] = []
    for root, _, files in os.walk("."):
        if root[:3] != ".\\." and not root.startswith(".\\venv"):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    module_name = file[:-3]
                    module = importlib.import_module(
                        f"{root.replace(os.path.sep, '.')[2:]}.{module_name}"
                    )
                    for _, obj in inspect.getmembers(
                        module,
                        lambda x: (
                            inspect.isclass(x)
                            and type(x).__name__ == TestMeta.__name__
                            and x.__name__ != "Test"
                        ),
                    ):
                        test_classes.append(obj)
    return test_classes


class TestRunner:
    def __init__(self) -> None:
        self.tests: List["TestMeta"] = []

    @patch("core.data.pickle.load")
    async def run(self, pickle_load: MagicMock):
        mock_data(pickle_load)
        tests = load_test_classes()

        await asyncio.sleep(1)
        if (await query_channel("With a hey, ho", get_test_channel()))[
            1
        ].content == ":notes: the wind and the rain :notes:":
            green("Successfully linked bots.")
        else:
            red("Impostor")

        ok, tot = 0, 0

        for test_cls in tests:
            test = test_cls()
            for attr in dir(test):
                if attr.startswith("test_"):
                    yellow(f"Running {attr}.")
                    try:
                        await getattr(test, attr)()
                    except Exception:
                        red(f"[X] Failed {attr}.")
                        red(traceback.format_exc())
                    else:
                        green(f"[✓] Passed {attr}.")
                        ok += 1
                    tot += 1

                    reset_data()
                    now.suppose_it_is(dt.now())

        color: Color = green if ok == tot else red
        color(f"Passed {ok}/{tot} tests.")
        exit(0)


class TestMeta(type):
    ...


class Test(metaclass=TestMeta):
    def assert_equal(self, x: Any, y: Any):
        if x != y:
            for i, s in enumerate(difflib.ndiff(x, y)):
                if s[0] == " ":
                    continue
                elif s[0] == "-":
                    print('Delete "{}" from position {}'.format(s[-1], i))
                elif s[0] == "+":
                    print('Add "{}" to position {}'.format(s[-1], i))
            raise AssertionError(
                f"These objects are not equal:\n{sep}\n{x}\n{sep}\n{y}\n{sep}"
            )

    def assert_geq(self, x: int, y: int):
        if x < y:
            raise AssertionError(f"{x} is not >= {y}.")

    def assert_true(self, x: bool):
        if not x:
            raise AssertionError(f"{x} is very much not True.")

    def assert_is_instance(self, x: Any, y: type):
        if not isinstance(x, y):
            raise AssertionError(f"{x} of type {type(x)} is not an instance of {y}.")

    def assert_dict_subset(self, x: Dict[Any, Any], y: Dict[Any, Any]):
        if not all(k in y.keys() and y[k] == v for k, v in x.items()):
            res = (
                f"Former dict is not a subset of latter:\n{sep}\n{x}\n{sep}\n{y}\n{sep}"
            )
            mismatch = {k: v for (k, v) in x.items() if k not in y.keys() or y[k] != v}
            res += f"\nMismatch:\n{sep}\n{mismatch}\n{sep}"
            raise AssertionError(mismatch)

    def assert_starts_with(self, x: str, y: str):
        if not x.startswith(y):
            raise AssertionError(
                f"Former str does not start with latter:\n{sep}\n{x}\n{sep}\n{y}\n{sep}"
            )

    def assert_len(self, x: Measureable, y: int):
        if not len(x) == y:
            raise AssertionError(
                f"Container does not have length {y}:\n{sep}\n{x}\n{sep}"
            )


@test_client.event
async def on_ready():
    if not test_client.guilds:
        print(f"{test_client.user} is not connected to any guilds.")
    else:
        print(
            f"{test_client.user} is connected to "
            f"{', '.join(guild.name for guild in test_client.guilds)}."
        )


async def start():
    try:
        await asyncio.gather(
            test_client.start(TEST_TOKEN), TestRunner().run(), start_bot()
        )
    except SystemExit:
        ...


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(start())


if __name__ == "__main__":
    main()
