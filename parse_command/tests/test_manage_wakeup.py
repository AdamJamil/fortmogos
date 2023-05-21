from core.bot import data
from core.timer import now
from core.utils.constants import get_test_channel
from core.utils.message import next_msg
from tests.main import Test

from tests.utils import query_channel
from core.utils.constants import testmogus_id, fakemogus_id


class TestManageWakeup(Test):
    async def test_manage_wakeup(self) -> None:
        data.wakeup.clear()

        test_channel = get_test_channel()

        _, _ = await query_channel("todo gamine", test_channel)
        _, response = await query_channel("wakeup 8am", test_channel)

        self.assert_equal(
            response.content,
            f"Got it, <@{testmogus_id}>, your wakeup time was set to 8AM.",
        )

        # 12 UTC is 8 EST
        now.suppose_it_is(now().replace(hour=11, minute=59, second=59))

        assert (
            alert := await next_msg(test_channel, fakemogus_id, is_not=response)
        ), "Timed out waiting for response."
        self.assert_equal(
            alert.content,
            """Good morning, <@1074389982095089664>! Here is your current todo list:
```
1) gamine
```""",
        )
