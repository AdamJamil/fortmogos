from datetime import datetime as dt, time as Time

import pytz
from tests.main import Test
from core.utils.time import parse_duration, parse_time


class TestTimeUtils(Test):
    async def test_parse_duration(self) -> None:
        ref = dt(year=2023, month=1, day=1)
        self.assert_equal(
            parse_duration("8m", ref), dt(year=2023, month=1, day=1, minute=8)
        )
        self.assert_equal(
            parse_duration("3d8m", ref), dt(year=2023, month=1, day=4, minute=8)
        )
        self.assert_equal(parse_duration("4n", ref), dt(year=2023, month=5, day=1))
        self.assert_equal(parse_duration("2y4n", ref), dt(year=2025, month=5, day=1))

        self.assert_equal(
            parse_duration("23", ref),
            "Didn't find a time unit corresponding to the value `23`.",
        )
        self.assert_equal(
            parse_duration("23g", ref),
            "`g` is not a valid unit of time.",
        )

    async def test_parse_time(self) -> None:
        est = pytz.timezone("US/Eastern")
        self.assert_is_instance(parse_time("1:48pm", est), Time)
        self.assert_is_instance(parse_time("11:48pm", est), Time)
        self.assert_is_instance(parse_time("1pm", est), Time)

        self.assert_is_instance(parse_time("111:48pm", est), str)
        self.assert_is_instance(parse_time(":428pm", est), str)
