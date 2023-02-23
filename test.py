from __future__ import annotations
import asyncio
import datetime
import traceback
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple
from datetime import datetime as dt, timedelta
from unittest.mock import MagicMock, patch

import discord
from bot import start as start_bot, data
from core.data import PersistentInfo
from core.task import PeriodicAlert, SingleAlert
from core.timer import now
from core.utils import parse_duration
from custom_typing.protocols import Color

if TYPE_CHECKING:
    from discord import PartialMessageable
    from discord.message import Message


client = discord.Client(intents=discord.Intents.all())


with open("token.txt", "r") as f:
    TOKEN = f.read().strip().split("\n")[1]


@client.event
async def on_ready():
    if not client.guilds:
        print(f"{client.user} is not connected to any guilds.")
    else:
        print(
            f"{client.user} is connected to "
            f"{', '.join(guild.name for guild in client.guilds)}."
        )


async def message_deleted(
    orig_channel: discord.channel.PartialMessageable, msg: Message
) -> bool:
    try:
        await orig_channel.fetch_message(msg.id)
    except discord.NotFound:
        return True
    return False


def green(x: str, **kwargs: Any):
    print(f"\033[38;2;20;255;20m{x}\033[0m", **kwargs)


def yellow(x: str, **kwargs: Any):
    print(f"\033[38;2;255;255;20m{x}\033[0m", **kwargs)


def red(x: str, **kwargs: Any):
    print(f"\033[38;2;255;20;20m{x}\033[0m", **kwargs)


def dict_subset(x: Dict[Any, Any], y: Dict[Any, Any]):
    return all(y[k] == v for k, v in x.items())


async def next_msg(
    channel: discord.PartialMessageable,
    user_id: int,
    is_not: Optional[Message] = None,
    sec: int = 3,
) -> Optional[Message]:
    for _ in range(sec):
        await asyncio.sleep(1)
        if (
            msg := await channel.history(limit=1).__anext__()
        ).author.id == user_id and msg != is_not:
            return msg
    return None


class Test:
    def __init__(self, channel: discord.PartialMessageable) -> None:
        self.channel = channel

    @staticmethod
    async def query(txt: str, channel: PartialMessageable) -> Tuple[Message, Message]:
        query = await channel.send(txt)

        assert (
            response := await next_msg(channel, 1061719682773688391, is_not=query)
        ), "Timed out waiting for response."

        return query, response

    @staticmethod
    def mock_data(pickle_load: MagicMock) -> None:
        pickle_load.return_value = PersistentInfo.__new__(PersistentInfo)
        pickle_load.return_value.tasks = []
        pickle_load.return_value.alert_channels = []

    @staticmethod
    def reset_data() -> None:
        data.tasks = []
        data.alert_channels = []

    @patch("core.data.pickle.load")
    async def run(self, pickle_load: MagicMock):
        Test.mock_data(pickle_load)

        await asyncio.sleep(2)
        if (await Test.query("With a hey, ho", self.channel))[
            1
        ].content == ":notes: the wind and the rain :notes:":
            green("Successfully linked bots.")
        else:
            red("Impostor")

        ok, tot = 0, 0

        for attr in dir(self):
            if attr.startswith("test_"):
                yellow(f"Running {attr}.")
                try:
                    await getattr(self, attr)()
                except Exception:
                    red(f"[X] Failed {attr}.")
                    red(traceback.format_exc())
                else:
                    green(f"[✓] Passed {attr}.")
                    ok += 1
                tot += 1

                Test.reset_data()
                now.suppose_it_is(dt.now())

        color: Color = green if ok == tot else red
        color(f"Passed {ok}/{tot} tests.")
        exit(0)

    async def test_set_daily(self) -> None:
        query, response = await Test.query("daily 8am wake up", self.channel)

        await asyncio.sleep(1)
        assert await message_deleted(self.channel, query)

        assert len(data.tasks) == 1
        assert isinstance(data.tasks[0], PeriodicAlert)
        assert dict_subset(
            {
                "msg": "wake up",
                "user": 1074389982095089664,
                "channel_id": 1063934130397659236,
                "_repeat_activation_threshold": datetime.timedelta(seconds=30),
                "periodicity": datetime.timedelta(days=1),
            },
            data.tasks[0].__dict__,
        )
        assert data.tasks[0].first_activation.hour == 8
        assert data.tasks[0].first_activation.minute == 0

        now.suppose_it_is(now().replace(hour=7, minute=59, second=59))

        assert (
            alert := await next_msg(
                self.channel, 1061719682773688391, is_not=response, sec=10
            )
        ), "Timed out waiting for response."
        assert alert.content.startswith(
            "Hey <@1074389982095089664>, this is a reminder to wake up."
        )
        assert alert.content.split(". ")[1].split(" ")[3].startswith("08:00")

    async def test_set_in(self) -> None:
        query, response = await Test.query("in 3d8h5m4s wake up", self.channel)
        curr_time = dt.now()

        await asyncio.sleep(1)
        assert await message_deleted(self.channel, query)

        assert len(data.tasks) == 1
        assert isinstance(data.tasks[0], SingleAlert)
        assert dict_subset(
            {
                "_activation_threshold": datetime.timedelta(seconds=30),
                "repeatable": False,
                "msg": "wake up",
                "user": 1074389982095089664,
                "channel_id": 1063934130397659236,
                "_reminder_str": "Hey <@{user}>, this is a reminder to {msg}. It's currently {x}",
            },
            data.tasks[0].__dict__,
        )
        assert data.tasks[0].activation.hour == (curr_time.hour + 8) % 24
        assert data.tasks[0].activation.minute == (curr_time.minute + 5) % 60

        now.suppose_it_is(curr_time + timedelta(days=3, hours=8, minutes=5, seconds=2))

        assert (
            alert := await next_msg(
                self.channel, 1061719682773688391, is_not=response, sec=10
            )
        ), "Timed out waiting for response."
        assert alert.content.startswith(
            "Hey <@1074389982095089664>, this is a reminder to wake up."
        )

    async def test_help(self) -> None:
        _, response = await Test.query("help reminder", self.channel)

        assert len(response.content.split("\n")) >= 15

    async def test_parse_duration(self) -> None:
        ref = dt(year=2023, month=1, day=1)
        assert parse_duration("8m", ref) == dt(year=2023, month=1, day=1, minute=8)
        assert parse_duration("3d8m", ref) == dt(year=2023, month=1, day=4, minute=8)
        assert parse_duration("4n", ref) == dt(year=2023, month=5, day=1)
        assert parse_duration("2y4n", ref) == dt(year=2025, month=5, day=1)

        assert (
            parse_duration("23", ref) == "Couldn't find units for last time quantity "
            "`23`. A valid duration is written with no spaces, and alternates between "
            'numbers and units of time (e.g. "2d1h5s").'
        )
        assert (
            parse_duration("23g", ref) == "Found character `g` which isn't a valid unit"
            ' of time. The options are "y", "n" (month), "d", "h", "m", "s".'
        )


async def start(test_channel: PartialMessageable):
    try:
        await asyncio.gather(client.start(TOKEN), Test(test_channel).run(), start_bot())
    except SystemExit:
        ...


def main():
    test_channel_id = 1063934130397659236
    test_channel = client.get_partial_messageable(test_channel_id)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(start(test_channel))


if __name__ == "__main__":
    main()
