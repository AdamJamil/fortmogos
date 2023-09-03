from core.start import data
from disc.tests.main import Test
from datetime import time as Time
from disc.tests.utils import get_messages_at_time, user_says
from core.utils.constants import testmogus_id


class TestManageWakeup(Test):
    async def test_manage_wakeup(self) -> None:
        data.wakeup.clear()  # wakeup is set at the beginning of all tests

        responses = await user_says("todo gamine", expected_responses=2)
        self.assert_equal(
            {responses[0].content, responses[1].content},
            {
                "Your task to `gamine` was added to your list. "
                "Try `see tasks` to view it.",
                "Daily pings with your todo list will appear here, <@0>!\n"
                "`wakeup <time>` changes the time, `wakeup set` resets the channel, "
                "and `wakeup disable` shuts it up.",
            },
        )
        response = await user_says("wakeup 8am", expected_responses=1)

        self.assert_equal(
            response.content,
            f"Got it, <@{testmogus_id}>, your wakeup time was set to 8AM.",
        )

        # 12 UTC is 8 EST
        alert = await get_messages_at_time(Time(hour=12), expected_messages=1)

        self.assert_equal(
            alert.content,
            f"""Good morning, <@{testmogus_id}>! Here is your current todo list:
```
1) gamine
```""",
        )
