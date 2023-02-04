import asyncio
from datetime import datetime as dt
from typing import TYPE_CHECKING, List

from core.data import PersistentInfo


start = dt.now()
speed_factor = 1000


def now() -> dt:
    if speed_factor == 1:
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
        while 1:
            print(f"It's currently {' '.join(str(now()).split(' ')[1:])}")
            if TYPE_CHECKING:
                from alert import Alert
            new_alerts: List[Alert] = []
            for task in self.data.alerts:
                if not await task.maybe_activate(self.timer) or task.repeats:
                    new_alerts.append(task)
            self.data.alerts = new_alerts

            await asyncio.sleep(max(0, 0.01 - (now() - self.timer).total_seconds()))
            self.timer = now()
