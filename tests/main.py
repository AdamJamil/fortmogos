from __future__ import annotations

import difflib
import importlib
import asyncio
import inspect
import os
import sys
import traceback
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch


from core.utils.constants import (
    TEST_TOKEN,
    get_test_channel,
    test_client,
    sep,
)
from tests.utils import query_channel, reset_data, mock_get_token
from core.bot import start as start_bot, data
from core.utils.color import green, red, yellow
from custom_typing.protocols import Color, Measureable


def load_test_classes() -> List[type]:
    test_classes: List[type] = []
    for root, _, files in os.walk("."):
        if root[:3] != ".\\." and "venv" not in root:
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

    @patch("core.bot.get_token")
    async def run(self, get_token: MagicMock):
        mock_get_token(get_token)

        tests = load_test_classes()

        while not hasattr(data, "timezones"):
            await asyncio.sleep(0.4)

        await asyncio.sleep(1)
        if (await query_channel("With a hey, ho", get_test_channel()))[
            1
        ].content == ":notes: the wind and the rain :notes:":
            green("Successfully linked bots.")
        else:
            red("Impostor")

        reset_data()

        # await asyncio.sleep(10**20)

        ok, tot = 0, 0

        for test_cls in tests:
            test = test_cls()
            for attr in dir(test):
                if attr.startswith("test_"):
                    if len(sys.argv) == 2 and not attr.startswith(sys.argv[1]):
                        continue
                    reset_data()
                    yellow(f"[🏃] Running {attr}.")
                    try:
                        await getattr(test, attr)()
                    except Exception:
                        red(f"[X] Failed {attr}.")
                        red(traceback.format_exc())
                    else:
                        green(f"[✓] Passed {attr}.")
                        ok += 1
                    tot += 1

        color: Color = green if ok == tot else red
        color(f"Passed {ok}/{tot} tests.")
        exit(0)


class TestMeta(type):
    ...


class Test(metaclass=TestMeta):
    def assert_equal(self, x: Any, y: Any):
        if type(x) == type(y) == dict:
            self.assert_dict_equal(x, y)
            return
        if x != y:
            if type(x) == type(y) == str:
                res = ""
                for i, s in enumerate(difflib.ndiff(x, y)):
                    if s[0] == " ":
                        continue
                    elif s[0] == "-":
                        res += 'Delete "{}" from position {}'.format(s[-1], i) + "\n"
                    elif s[0] == "+":
                        res += 'Add "{}" to position {}'.format(s[-1], i) + "\n"
                if len(res.split("\n")) > 30:
                    print("str difference too large to print")
                else:
                    print(res)
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

    def assert_dict_equal(self, x: Dict[Any, Any], y: Dict[Any, Any]):
        self.assert_dict_subset(x, y)
        self.assert_dict_subset(y, x)

    def assert_dict_subset(self, x: Dict[Any, Any], y: Dict[Any, Any]):
        if not all(k in y.keys() and y[k] == v for k, v in x.items()):
            res = (
                f"Former dict is not a subset of latter:\n{sep.ins('Former')}\n{x}"
                f"\n{sep.ins('Latter')}\n{y}\n"
            )
            mismatch = {k: v for (k, v) in x.items() if k not in y.keys() or y[k] != v}
            res += f"{sep.ins('Mismatch')}\n{mismatch}\n{sep}"
            raise AssertionError(res)

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

    def assert_has_attrs(self, x: Any, y: Dict[str, Any]):
        mismatch = ""
        for k, v in y.items():
            if not hasattr(x, k):
                mismatch += f"Missing field {k}.\n"
            elif (av := getattr(x, k)) != v:
                mismatch += f"{k}:\n    Expected: {v}\n    Got: {av}\n"
        if mismatch:
            res = f"Object fields are incorrect:\n{mismatch}"
            raise AssertionError(res)


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
