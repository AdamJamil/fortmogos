from __future__ import annotations

import importlib
import asyncio
import inspect
import os
import traceback
from typing import List
from datetime import datetime as dt
from unittest.mock import MagicMock, patch


from core.utils.constants import TEST_TOKEN, get_test_channel, test_client
from tests.utils import mock_data, query_channel, reset_data
from core.bot import start as start_bot
from core.timer import now
from core.utils.color import green, red, yellow
from custom_typing.protocols import Color


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
    ...


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
