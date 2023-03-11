import datetime
from core.utils.constants import get_test_channel
from tests.main import Test

from tests.utils import query_channel


class TestManageReminder(Test):
    async def test_manage_reminders(self) -> None:
        test_channel = get_test_channel()

        _, _ = await query_channel("daily 8am wake up", test_channel)
        _, response = await query_channel("see reminders", test_channel)
        day = "Tomorrow" if datetime.datetime.now().hour >= 8 else "Today"
        self.assert_equal(
            response.content,
            f"""Here are your reminders, <@1074389982095089664>.
```
{day}
  8AM [daily]: wake up

```""",
        )

        _, response = await query_channel("delete 1", test_channel)
        self.assert_equal(
            response.content, "Hey <@{msg.author.id}>, you're an idiot :D"
        )

        _, response = await query_channel("delete 0", test_channel)
        self.assert_equal(
            response.content, "Hey <@1074389982095089664>, your alert was deleted."
        )

        _, response = await query_channel("see reminders", test_channel)
        print(response.content)
        self.assert_equal(
            response.content, "You have no reminders, <@1074389982095089664>."
        )
