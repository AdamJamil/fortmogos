import asyncio
from datetime import datetime as dt, timedelta
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from core.data import PersistentInfo


class Now:
    def __init__(self) -> None:
        self.offset: timedelta = timedelta()

    def __call__(self, do_not_mock: bool = False) -> dt:
        return dt.now() + self.offset

    def suppose_it_is(self, new_time: dt) -> None:
        # new_time = now + offset
        self.offset = new_time - dt.now()


now = Now()


class Timer:
    def __init__(self, data: "PersistentInfo"):
        self.timer = now()
        self.data = data

    async def run(self):
        if self.data.alert_channels:
            await asyncio.gather(
                *(channel.send("nyooooom") for channel in self.data.alert_channels)
            )

        while 1:
            print(f"It's currently {' '.join(str(now()).split(' ')[1:])}")
            self.data.tasks = [
                task
                for task in self.data.tasks
                if not await task.maybe_activate(self.timer) or task.repeatable
            ]

            await asyncio.sleep(max(0, 0.5 - (now() - self.timer).total_seconds()))
            self.timer = now()
