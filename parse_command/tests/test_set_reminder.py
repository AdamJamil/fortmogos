import asyncio
from typing import cast
from core.utils.constants import (
    get_test_channel,
    test_channel_id,
    fakemogus_id,
    testmogus_id,
)
from tests.main import Test

import datetime
from datetime import datetime as dt, timedelta
from tests.utils import query_channel
from core.utils.message import message_deleted, next_msg
from core.bot import data
from core.data.writable import PeriodicAlert, SingleAlert
from core.timer import now


class TestSetReminder(Test):
    async def test_set_daily(self) -> None:
        test_channel = get_test_channel()
        query, response = await query_channel("daily 8am wake up", test_channel)

        await asyncio.sleep(0.2)  # TODO(remove this sleep and turn into wait delete)
        self.assert_true(await message_deleted(test_channel, query))

        self.assert_len(data.tasks, 1)
        self.assert_is_instance(data.tasks[0], PeriodicAlert)
        self.assert_has_attrs(
            data.tasks[0],
            {
                "msg": "wake up",
                "user": testmogus_id,
                "channel_id": test_channel_id,
                "_repeat_activation_threshold": datetime.timedelta(seconds=60),
                "periodicity": datetime.timedelta(days=1),
            },
        )
        self.assert_equal(cast(PeriodicAlert, data.tasks[0]).first_activation.hour, 8)
        self.assert_equal(cast(PeriodicAlert, data.tasks[0]).first_activation.minute, 0)

        now.suppose_it_is(now().replace(hour=7, minute=59, second=59))

        assert (
            alert := await next_msg(test_channel, fakemogus_id, is_not=response, sec=10)
        ), "Timed out waiting for response."
        self.assert_starts_with(
            alert.content, f"Hey <@{testmogus_id}>, this is a reminder to wake up."
        )
        self.assert_starts_with(alert.content.split(". ")[1].split(" ")[3], "08:00")

    async def test_set_in(self) -> None:
        test_channel = get_test_channel()
        query, response = await query_channel("in 3d8h5m4s wake up", test_channel)
        curr_time = dt.now()

        await asyncio.sleep(0.2)
        self.assert_true(await message_deleted(test_channel, query))

        self.assert_len(data.tasks, 1)
        self.assert_is_instance(data.tasks[0], SingleAlert)
        self.assert_has_attrs(
            data.tasks[0],
            {
                "_activation_threshold": datetime.timedelta(seconds=30),
                "repeatable": False,
                "msg": "wake up",
                "user": testmogus_id,
                "channel_id": test_channel_id,
                "_reminder_str": (
                    "Hey <@{user}>, this is a reminder to {msg}. It's currently {x}"
                ),
            },
        )
        self.assert_equal(
            cast(SingleAlert, data.tasks[0]).activation.hour,
            (
                (
                    curr_time.hour
                    + 8
                    + (curr_time.minute + 5 + (curr_time.second + 4 >= 60) >= 60)
                )
                % 24
            ),
        )
        # TODO(failure sometimes)
        self.assert_equal(
            cast(SingleAlert, data.tasks[0]).activation.minute,
            ((curr_time.minute + 5 + (curr_time.second + 4 >= 60)) % 60),
        )

        now.suppose_it_is(curr_time + timedelta(days=3, hours=8, minutes=5, seconds=2))

        assert (
            alert := await next_msg(test_channel, fakemogus_id, is_not=response, sec=10)
        ), "Timed out waiting for response."
        self.assert_starts_with(
            alert.content, f"Hey <@{testmogus_id}>, this is a reminder to wake up."
        )
