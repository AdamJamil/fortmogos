import asyncio
from core.utils.constants import get_test_channel
from core.utils.message import next_msg
from tests.main import Test

from tests.utils import query_channel, query_message_with_reaction
from core.utils.constants import fakemogus_id, todo_emoji, testmogus_id


class TestManageReminder(Test):
    async def test_manage_reaction(self) -> None:
        test_channel = get_test_channel()

        _, response = await query_channel("in 1s gamingos", test_channel)

        await asyncio.sleep(1.2)
        assert (
            alert := await next_msg(test_channel, fakemogus_id, is_not=response)
        ), "Timed out waiting for response."
        self.assert_len(alert.reactions, 1)
        self.assert_equal(alert.reactions[0].emoji, todo_emoji)

        update = await query_message_with_reaction(todo_emoji, alert, test_channel)
        self.assert_equal(
            update.content,
            (
                f"Got it, <@{testmogus_id}>. Your reminder to gamingos "
                "was added to your todo list."
            ),
        )
