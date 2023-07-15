from core.utils.constants import get_test_channel
from tests.main import Test
from tests.utils import query_channel


class TestHelp(Test):
    async def test_help(self) -> None:
        _, response = await query_channel("help reminder", get_test_channel())

        self.assert_geq(len(response.content.split("\n")), 15)
