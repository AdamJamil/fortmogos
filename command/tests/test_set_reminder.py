from typing import cast

import pytz

from core.utils.constants import testmogus_id
from disc.tests.main import Test

from datetime import timedelta, time as Time
from disc.tests.utils import (
    get_messages_at_time,
    test_message_deleted,
    user_says,
)
from core.start import data
from core.data.writable import MonthlyAlert, PeriodicAlert, SingleAlert
from core.timer import now


class TestSetReminder(Test):
    async def test_set_daily(self) -> None:
        response = await user_says("daily 8am wake up", expected_responses=1)
        self.assert_equal(
            response.content,
            f'<@{testmogus_id}>\'s daily reminder at 8AM to "wake up" has been set.',
        )

        self.assert_true(test_message_deleted("daily 8am wake up"))

        self.assert_len(data.tasks, 1)
        self.assert_is_instance(data.tasks[0], PeriodicAlert)
        self.assert_has_attrs(
            data.tasks[0],
            {
                "msg": "wake up",
                "user": testmogus_id,
                "_repeat_activation_threshold": timedelta(seconds=60),
                "periodicity": timedelta(days=1),
            },
        )
        task_activation = cast(
            PeriodicAlert, data.tasks[0]
        ).first_activation.astimezone(data.timezones[testmogus_id].tz)
        self.assert_equal(task_activation.hour, 12)
        self.assert_equal(task_activation.minute, 0)

        # 12 UTC is 8 EST
        alert = await get_messages_at_time(
            Time(hour=12, minute=0, second=0), expected_messages=1
        )
        self.assert_starts_with(
            alert.content, f"Hey <@{testmogus_id}>, this is a reminder to wake up."
        )

        await get_messages_at_time(
            Time(hour=12, minute=0, second=2), expected_messages=0
        )

    async def test_set_weekly(self) -> None:
        response = await user_says("weekly 8am tuesdAy trash", expected_responses=1)
        self.assert_equal(
            response.content,
            (
                f'<@{testmogus_id}>\'s weekly reminder at 8AM on Tuesdays to "trash" '
                "has been set."
            ),
        )

        self.assert_true(test_message_deleted("weekly 8am tuesdAy trash"))

        self.assert_len(data.tasks, 1)
        self.assert_is_instance(data.tasks[0], PeriodicAlert)
        self.assert_has_attrs(
            data.tasks[0],
            {
                "msg": "trash",
                "user": testmogus_id,
                "_repeat_activation_threshold": timedelta(seconds=60),
                "periodicity": timedelta(days=7),
            },
        )
        task_activation = (
            cast(PeriodicAlert, data.tasks[0])
            .first_activation.replace(tzinfo=pytz.UTC)
            .astimezone(pytz.timezone("US/Eastern"))
        )
        self.assert_equal(task_activation.hour, 8)
        self.assert_equal(task_activation.minute, 0)
        now.suppose_it_is(now().replace(hour=12))
        start = now()

        for i in range(14):
            curr = start + timedelta(days=i)
            if curr.strftime("%A") == "Tuesday":
                alert = await get_messages_at_time(curr, expected_messages=1)
                self.assert_equal(
                    alert.content,
                    f"Hey <@{testmogus_id}>, this is a reminder to trash.",
                )
            else:
                await get_messages_at_time(curr, expected_messages=0)

    async def test_set_monthly(self) -> None:
        response = await user_says("monthly 8am 7th trash", expected_responses=1)
        self.assert_equal(
            response.content,
            (
                f"<@{testmogus_id}>'s monthly reminder on the 7th of each month at "
                '8AM to "trash" has been set.'
            ),
        )

        self.assert_true(test_message_deleted("monthly 8am 7th trash"))

        self.assert_len(data.tasks, 1)
        self.assert_is_instance(data.tasks[0], MonthlyAlert)
        self.assert_has_attrs(
            data.tasks[0],
            {
                "msg": "trash",
                "user": testmogus_id,
                "day": 7,
                "time": Time(hour=12),
            },
        )
        now.suppose_it_is(now().replace(hour=12))
        start = now()
        curr = start

        i = 0
        while i <= 200:
            curr = start + timedelta(days=i)
            if int(curr.strftime("%d")) == 7:
                alert = await get_messages_at_time(curr, expected_messages=1)
                self.assert_equal(
                    alert.content,
                    f"Hey <@{testmogus_id}>, this is a reminder to trash.",
                )
                if i > 30:
                    i += 25
            else:
                await get_messages_at_time(curr, expected_messages=0)
            i += 1

    async def test_set_monthly_end(self) -> None:
        response = await user_says("monthly 30th 8am trash", expected_responses=1)
        self.assert_equal(
            response.content,
            (
                f"<@{testmogus_id}>'s monthly reminder on the 30th of each month at "
                '8AM to "trash" has been set.'
            ),
        )

        self.assert_true(test_message_deleted("monthly 30th 8am trash"))

        self.assert_len(data.tasks, 1)
        self.assert_is_instance(data.tasks[0], MonthlyAlert)
        self.assert_has_attrs(
            data.tasks[0],
            {
                "msg": "trash",
                "user": testmogus_id,
                "day": 30,
                "time": Time(hour=12),
            },
        )
        now.suppose_it_is(now().replace(hour=12))
        start = now()
        curr = start

        i = 0
        while i <= 70:
            curr = start + timedelta(days=i)
            curr_day = int(curr.strftime("%d"))
            next_day = int((curr + timedelta(days=1)).strftime("%d"))
            if curr_day == 30 or next_day != curr_day + 1:
                alert = await get_messages_at_time(curr, expected_messages=1)
                self.assert_equal(
                    alert.content,
                    f"Hey <@{testmogus_id}>, this is a reminder to trash.",
                )
                if i > 30:
                    i += 25
            else:
                await get_messages_at_time(curr, expected_messages=0)
            i += 1

    async def test_set_in(self) -> None:
        response = await user_says("in 3d8h5m4s wake up", expected_responses=1)
        curr_time = now()

        self.assert_starts_with(
            response.content,
            f"<@{testmogus_id}>'s reminder on ",
        )
        self.assert_ends_with(response.content, ' to "wake up" has been set.')
        self.assert_true(test_message_deleted("in 3d8h5m4s wake up"))

        self.assert_len(data.tasks, 1)
        self.assert_is_instance(data.tasks[0], SingleAlert)
        self.assert_has_attrs(
            data.tasks[0],
            {
                "_activation_threshold": timedelta(seconds=30),
                "repeatable": False,
                "msg": "wake up",
                "user": testmogus_id,
                "_reminder_str": ("Hey <@{user}>, this is a reminder to {msg}."),
            },
        )

        activation = cast(SingleAlert, data.tasks[0]).activation
        delta = timedelta(days=3, hours=8, minutes=5, seconds=4)
        self.assert_geq(
            1,
            int((curr_time - activation + delta).total_seconds()),
        )

        alert = await get_messages_at_time(curr_time + delta, expected_messages=1)
        self.assert_starts_with(
            alert.content, f"Hey <@{testmogus_id}>, this is a reminder to wake up."
        )
