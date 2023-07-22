from tests.main import Test

from tests.utils import user_says
from core.utils.constants import testmogus_id


class TestManageTask(Test):
    async def test_manage_task(self) -> None:
        response = await user_says("task do laundry", expected_responses=1)

        self.assert_equal(
            response.content,
            (
                "Your task to `do laundry` was added to your list. "
                "Try `see tasks` to view it."
            ),
        )

        response = await user_says("see tasks", expected_responses=1)
        self.assert_equal(
            response.content,
            f"Here is your todo list, <@{testmogus_id}>:\n```\n1) do laundry\n```",
        )

        response = await user_says("delete task 1", expected_responses=1)
        self.assert_equal(
            response.content,
            f"Hey <@{testmogus_id}>, your task `do laundry` was deleted.",
        )

        response = await user_says("see tasks", expected_responses=1)
        self.assert_equal(response.content, "Your todo list is empty.")
