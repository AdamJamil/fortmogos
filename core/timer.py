import asyncio
from datetime import datetime as dt, timedelta
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from core.data import PersistentInfo


class Now:
    def __init__(self) -> None:
        self.start: dt = dt.now()
        self.speed_factor: int = 1

    def __call__(self, do_not_mock: bool = False) -> dt:
        if do_not_mock or self.speed_factor == 1:
            return dt.now()
        return self.start + self.speed_factor * (dt.now() - self.start)

    def suppose_it_is(self, new_time: dt) -> None:
        # new_time = start + sf * (now - start)
        #        = (1 - sf) * start + sf * now
        # start  = (new_time - sf * now) / (1 - sf)
        curr = dt.now()
        curr_epoch = (curr - dt(1970, 1, 1)).total_seconds()
        new_time_epoch = (new_time - dt(1970, 1, 1)).total_seconds()
        start_epoch = (new_time_epoch - self.speed_factor * curr_epoch) / (
            1 - self.speed_factor
        )
        self.start = dt(1970, 1, 1) + timedelta(seconds=start_epoch)


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
            # print(f"It's currently {' '.join(str(now()).split(' ')[1:])}")
            self.data.tasks = [
                task
                for task in self.data.tasks
                if not await task.maybe_activate(self.timer) or task.repeatable
            ]

            await asyncio.sleep(max(0, 0.5 - (now() - self.timer).total_seconds()))
            self.timer = now()
