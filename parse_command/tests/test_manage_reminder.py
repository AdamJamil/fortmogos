from core.utils.constants import get_test_channel
from tests.main import Test

from tests.utils import query_channel


class TestManageReminder(Test):
    async def test_show_reminders(self) -> None:
        test_channel = get_test_channel()

        _, _ = await query_channel("daily 8am wake up", test_channel)
        _, response = await query_channel("see reminders", test_channel)
        print(response.content)
        assert (
            response.content
            == """Here are your reminders, <@1074389982095089664>.
```
Today
  8AM [daily]: wake up

```"""
        )
