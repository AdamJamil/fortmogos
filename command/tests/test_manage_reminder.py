from core.timer import now
from tests.main import Test

from tests.utils import user_says
from core.utils.constants import testmogus_id


class TestManageReminder(Test):
    async def test_manage_reminders(self) -> None:
        response = await user_says("daily 8am wake up", expected_responses=1)
        self.assert_equal(
            response.content,
            f'<@{testmogus_id}>\'s daily reminder at 8AM to "wake up" has been set.',
        )

        now.suppose_it_is(now().replace(hour=13, minute=0, second=0))
        response = await user_says("see reminders", expected_responses=1)
        self.assert_equal(
            response.content,
            f"""Here are your reminders, <@{testmogus_id}>.
```
Tomorrow
  8AM [daily]: wake up

```""",
        )

        response = await user_says("delete reminder 2", expected_responses=1)
        self.assert_equal(
            response.content, f"Hey <@{testmogus_id}>, you're an idiot :D"
        )

        response = await user_says("delete reminder 1", expected_responses=1)
        self.assert_equal(
            response.content,
            (
                f"Hey <@{testmogus_id}>, your daily reminder"
                " at 8AM to wake up was deleted."
            ),
        )

        response = await user_says("see reminders", expected_responses=1)
        self.assert_equal(
            response.content, f"You have no reminders, <@{testmogus_id}>."
        )
