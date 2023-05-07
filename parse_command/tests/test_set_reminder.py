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
from datetime import timedelta
from tests.utils import query_channel
from core.utils.message import message_deleted, next_msg
from core.bot import data
from core.data.writable import PeriodicAlert, SingleAlert
from core.timer import now


class TestSetReminder(Test):
    async def test_set_daily(self) -> None:
        test_channel = get_test_channel()
        query, response = await query_channel("daily 8am wake up", test_channel)
        self.assert_equal(
            response.content,
            f'<@{testmogus_id}>\'s daily reminder at 8AM to "wake up" has been set.',
        )

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
        task_activation = cast(
            PeriodicAlert, data.tasks[0]
        ).first_activation.astimezone(data.timezones[query.author.id].tz)
        self.assert_equal(task_activation.hour, 12)
        self.assert_equal(task_activation.minute, 0)

        # 12 UTC is 8 EST
        now.suppose_it_is(now().replace(hour=11, minute=59, second=59))

        assert (
            alert := await next_msg(test_channel, fakemogus_id, is_not=response)
        ), "Timed out waiting for response."
        self.assert_starts_with(
            alert.content, f"Hey <@{testmogus_id}>, this is a reminder to wake up."
        )
        self.assert_starts_with(alert.content.split(". ")[1].split(" ")[2], "8AM")

        now.set_speed(2 * 60 / 2)  # 2 minutes should go by in 2 seconds
        maybe_alert = await next_msg(test_channel, fakemogus_id, is_not=alert, sec=2)

        assert maybe_alert is None, "Got an alert somehow"

    async def test_set_in(self) -> None:
        test_channel = get_test_channel()
        query, response = await query_channel("in 3d8h5m4s wake up", test_channel)
        curr_time = now()

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
                    "Hey <@{user}>, this is a reminder to {msg}. It's currently {x}."
                ),
            },
        )

        activation = cast(SingleAlert, data.tasks[0]).activation
        delta = timedelta(days=3, hours=8, minutes=5, seconds=4)
        self.assert_geq(
            5,
            int((curr_time - activation + delta).total_seconds()),
        )

        now.suppose_it_is(curr_time + delta)

        assert (
            alert := await next_msg(test_channel, fakemogus_id, is_not=response)
        ), "Timed out waiting for response."
        self.assert_starts_with(
            alert.content, f"Hey <@{testmogus_id}>, this is a reminder to wake up."
        )
