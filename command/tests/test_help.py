from disc.tests.main import Test
from disc.tests.utils import user_says


class TestHelp(Test):
    async def test_help(self) -> None:
        response = await user_says("help reminder", expected_responses=1)
        self.assert_equal(len(response.content.split("\n")), 1)
