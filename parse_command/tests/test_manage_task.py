from core.utils.constants import get_test_channel
from tests.main import Test

from tests.utils import query_channel


class TestManageTask(Test):
    async def test_manage_task(self) -> None:
        test_channel = get_test_channel()

        query, _ = await query_channel("task do laundry", test_channel)
        _, response = await query_channel("see tasks", test_channel)
        self.assert_equal(
            response.content,
            f"Here is your todo list, <@{query.author.id}>:\n```\n1) do laundry\n```",
        )

        query, _ = await query_channel("delete task 1", test_channel)

        _, response = await query_channel("see tasks", test_channel)
        self.assert_equal(response.content, "Your todo list is empty.")
