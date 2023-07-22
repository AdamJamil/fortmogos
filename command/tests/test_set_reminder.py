from typing import cast

from core.utils.constants import (
    test_channel_id,
    testmogus_id,
)
from tests.main import Test

from datetime import timedelta, time as Time
from tests.utils import (
    get_messages_at_time,
    test_message_deleted,
    user_says,
)
from core.bot import data
from core.data.writable import PeriodicAlert, SingleAlert
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
                "channel_id": test_channel_id,
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
        self.assert_starts_with(alert.content.split(". ")[1].split(" ")[2], "8AM")

        await get_messages_at_time(
            Time(hour=12, minute=0, second=2), expected_messages=0
        )

    async def test_set_in(self) -> None:
        response = await user_says("in 3d8h5m4s wake up", expected_responses=1)
        curr_time = now()

        self.assert_starts_with(
            response.content,
            f"<@{testmogus_id}>'s reminder on the ",
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
                "channel_id": test_channel_id,
                "_reminder_str": (
                    "Hey <@{user}>, this is a reminder to {msg}. It's currently {x}."
                ),
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
