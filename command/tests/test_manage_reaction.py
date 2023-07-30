from core.timer import now
from disc.tests.main import Test
from datetime import timedelta
from disc.tests.utils import (
    get_messages_at_time,
    query_message_with_reaction,
    user_says,
)
from core.utils.constants import todo_emoji, testmogus_id


class TestManageReminder(Test):
    async def test_manage_reaction(self) -> None:
        await user_says("in 1s gamingos", expected_responses=1)

        now.suppose_it_is(now() + timedelta(seconds=1))

        alert = await get_messages_at_time(
            now() + timedelta(seconds=1), expected_messages=1
        )

        self.assert_len(alert.reactions, 1)
        self.assert_equal(alert.reactions[0].emoji, todo_emoji)

        response = await query_message_with_reaction(
            todo_emoji, alert, expected_messages=1
        )
        self.assert_equal(
            response.content,
            (
                f"Got it, <@{testmogus_id}>. Your reminder to gamingos was added to "
                "your todo list."
            ),
        )
