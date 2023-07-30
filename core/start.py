from __future__ import annotations

import asyncio
import traceback

from core.timer import Timer
from disc.start import start_discord
from core.data.handler import DataHandler


data = DataHandler()
data.populate_data()
timer = Timer(data)


async def get_awaitables():
    return await asyncio.gather(start_discord(), timer.run())


if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.run(get_awaitables())
    except (Exception, KeyboardInterrupt) as e:
        print(f"Caught {type(e)}, shutting down..")
        print(e)
        print(traceback.format_exc())
        exit(1)
