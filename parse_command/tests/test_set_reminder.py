from core.utils.constants import get_test_channel
from tests.main import Test

import asyncio
import datetime
from datetime import datetime as dt, timedelta
from tests.utils import dict_subset, query_channel
from core.utils.message import message_deleted, next_msg
from core.bot import data
from core.task import PeriodicAlert, SingleAlert
from core.timer import now


class TestSetReminder(Test):
    async def test_set_daily(self) -> None:
        test_channel = get_test_channel()
        query, response = await query_channel("daily 8am wake up", test_channel)

        await asyncio.sleep(1)
        assert await message_deleted(test_channel, query)

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
                test_channel, 1061719682773688391, is_not=response, sec=10
            )
        ), "Timed out waiting for response."
        assert alert.content.startswith(
            "Hey <@1074389982095089664>, this is a reminder to wake up."
        )
        assert alert.content.split(". ")[1].split(" ")[3].startswith("08:00")

    async def test_set_in(self) -> None:
        test_channel = get_test_channel()
        query, response = await query_channel("in 3d8h5m4s wake up", test_channel)
        curr_time = dt.now()

        await asyncio.sleep(1)
        assert await message_deleted(test_channel, query)

        assert len(data.tasks) == 1
        assert isinstance(data.tasks[0], SingleAlert)
        assert dict_subset(
            {
                "_activation_threshold": datetime.timedelta(seconds=30),
                "repeatable": False,
                "msg": "wake up",
                "user": 1074389982095089664,
                "channel_id": 1063934130397659236,
                "_reminder_str": (
                    "Hey <@{user}>, this is a reminder to {msg}. It's currently {x}"
                ),
            },
            data.tasks[0].__dict__,
        )
        assert data.tasks[0].activation.hour == (curr_time.hour + 8) % 24
        assert data.tasks[0].activation.minute == (curr_time.minute + 5) % 60

        now.suppose_it_is(curr_time + timedelta(days=3, hours=8, minutes=5, seconds=2))

        assert (
            alert := await next_msg(
                test_channel, 1061719682773688391, is_not=response, sec=10
            )
        ), "Timed out waiting for response."
        assert alert.content.startswith(
            "Hey <@1074389982095089664>, this is a reminder to wake up."
        )