import asyncio
from datetime import datetime as dt
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from core.data import PersistentInfo


start = dt.now()
speed_factor = 10000


def now(do_not_mock=False) -> dt:
    if do_not_mock or speed_factor == 1:
        return dt.now()
    return start + speed_factor * (dt.now() - start)


class Timer:
    def __init__(self, data):
        self.timer = now()
        self.data: PersistentInfo = data

    async def run(self):
        if self.data.alert_channels:
            await asyncio.gather(
                *(channel.send("nyooooom") for channel in self.data.alert_channels)
            )

        from core.task import RepeatableTask

        while 1:
            print(f"It's currently {' '.join(str(now()).split(' ')[1:])}")
            if TYPE_CHECKING:
                from core.task import Task
            new_tasks: List[Task] = []
            for task in self.data.tasks:
                if not await task.maybe_activate(self.timer) or isinstance(
                    task, RepeatableTask
                ):
                    new_tasks.append(task)
            self.data.tasks = new_tasks

            await asyncio.sleep(max(0, 0.1 - (now() - self.timer).total_seconds()))
            self.timer = now()
