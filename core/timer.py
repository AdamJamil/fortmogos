import asyncio
from datetime import datetime as dt, timedelta
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from core.data.handler import DataHandler
    from core.data.writable import Task


class Now:
    def __init__(self) -> None:
        self.start = dt.now()
        self.offset: timedelta = timedelta()
        self._speed = 1

    def __call__(self) -> dt:
        _now = dt.now()
        return _now + (self._speed - 1) * (_now - self.start) + self.offset

    def suppose_it_is(self, new_time: dt) -> None:
        # new_time = now + offset
        self.offset = new_time - dt.now()
        self.start = new_time - self.offset

    def set_speed(self, new_speed: float) -> None:
        self._speed = new_speed
        self.start = dt.now()


now = Now()


class Timer:
    def __init__(self, data: "DataHandler"):
        self.timer = now()
        self.data = data

    async def run(self):
        if self.data.alert_channels:
            await asyncio.gather(
                *(channel.send("nyooooom") for channel in self.data.alert_channels)
            )

        while 1:
            print(f"It's currently {' '.join(str(now()).split(' ')[1:])}")

            async def should_keep_task(task: "Task") -> bool:
                return not await task.maybe_activate(self.timer) or task.repeatable

            await self.data.tasks.async_filter(should_keep_task)

            await asyncio.sleep(max(0, 0.5 - (now() - self.timer).total_seconds()))
            self.timer = now()
