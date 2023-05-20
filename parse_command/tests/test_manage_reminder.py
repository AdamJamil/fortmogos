import datetime
from core.utils.constants import get_test_channel
from tests.main import Test

from tests.utils import query_channel
from core.bot import data
from core.utils.constants import testmogus_id


class TestManageReminder(Test):
    async def test_manage_reminders(self) -> None:
        test_channel = get_test_channel()

        _, _ = await query_channel("daily 8am wake up", test_channel)
        _, response = await query_channel("see reminders", test_channel)
        day = (
            "Tomorrow"
            if datetime.datetime.now(data.timezones[testmogus_id].tz).hour >= 8
            else "Today"
        )
        self.assert_equal(
            response.content,
            f"""Here are your reminders, <@1074389982095089664>.
```
{day}
  8AM [daily]: wake up

```""",
        )

        _, response = await query_channel("delete reminder 2", test_channel)
        self.assert_equal(
            response.content, "Hey <@1074389982095089664>, you're an idiot :D"
        )

        _, response = await query_channel("delete reminder 1", test_channel)
        self.assert_equal(
            response.content,
            (
                "Hey <@1074389982095089664>, your daily reminder"
                " at 12PM to wake up was deleted."
            ),
        )

        _, response = await query_channel("see reminders", test_channel)
        self.assert_equal(
            response.content, "You have no reminders, <@1074389982095089664>."
        )
