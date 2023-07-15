import asyncio
from datetime import datetime as dt, timedelta
from typing import TYPE_CHECKING

import pytz


if TYPE_CHECKING:
    from core.data.handler import DataHandler
    from core.data.writable import Task


class Now:
    def __init__(self) -> None:
        self.start = dt.now(tz=pytz.utc).replace(tzinfo=None)
        self.offset: timedelta = timedelta()
        self._speed: float = 1

    def __call__(self) -> dt:
        """
        Returns UTC time, but without timezone attached.
        """
        _now = dt.now(tz=pytz.utc).replace(tzinfo=None)
        return _now + (self._speed - 1) * (_now - self.start) + self.offset

    def suppose_it_is(self, new_time: dt) -> None:
        # new_time = now + offset
        self.offset = new_time - dt.now(tz=pytz.utc).replace(tzinfo=None)
        self.start = new_time - self.offset

    def set_speed(self, new_speed: float) -> None:
        self._speed = new_speed
        self.start = dt.now(tz=pytz.utc).replace(tzinfo=None)


now = Now()  # callable that returns UTC time, no timezone attached


class Timer:
    def __init__(self, data: "DataHandler"):
        self.timer = now()
        self.data = data

    async def run(self):
        while not hasattr(self.data, "alert_channels"):
            await asyncio.sleep(0.4)
        if self.data.alert_channels:
            await asyncio.gather(
                *(channel.send("nyooooom") for channel in self.data.alert_channels)
            )

        while "among":
            print(f"It's currently {' '.join(str(now()).split(' ')[1:])}")

            async def should_keep_task(task: "Task") -> bool:
                return not await task.maybe_activate(self.timer) or task.repeatable

            async def maybe_activate(_: int, task: "Task") -> None:
                await task.maybe_activate(self.timer)

            await self.data.tasks.async_filter(should_keep_task)
            await self.data.wakeup.async_lambda(maybe_activate)

            await asyncio.sleep(max(0, 0.5 - (now() - self.timer).total_seconds()))
            self.timer = now()
