from __future__ import annotations
import asyncio
import datetime
import traceback
from typing import TYPE_CHECKING, Any, Dict, Optional

import discord
from bot import start as start_bot, data
from core.task import PeriodicAlert
from core.timer import now
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

    async def run(self):
        await asyncio.sleep(2)
        while True:
            await self.channel.send("With a hey, ho")
            await asyncio.sleep(1)
            if (
                await self.channel.history(limit=1).__anext__()
            ).content == ":notes: the wind and the rain :notes:":
                break

        green("Successfully linked bots.")

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

        color: Color = green if ok == tot else red
        color(f"Passed {ok}/{tot} tests.")
        exit(0)

    async def test_set_daily(self) -> None:
        shit = await self.channel.send("daily 8am wake up")

        assert (
            response := await next_msg(self.channel, 1061719682773688391)
        ), "Timed out waiting for response."

        await asyncio.sleep(1)
        assert await message_deleted(self.channel, shit), "Message wasn't deleted."

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

        now.suppose_it_is(now().replace(hour=7, minute=30))

        assert (
            alert := await next_msg(
                self.channel, 1061719682773688391, is_not=response, sec=10
            )
        ), "Timed out waiting for response."
        print(alert.content)
        assert alert.content.startswith(
            "Hey <@1074389982095089664>, this is a reminder to wake up."
        )
        assert alert.content.split(". ")[1].split(" ")[3].startswith("08")


async def start(test_channel: PartialMessageable):
    try:
        await asyncio.gather(client.start(TOKEN), Test(test_channel).run(), start_bot())
    except SystemExit:
        ...


def main():
    now.speed_factor = 600

    test_channel_id = 1063934130397659236
    test_channel = client.get_partial_messageable(test_channel_id)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(start(test_channel))


if __name__ == "__main__":
    main()
