from datetime import datetime as dt
from tests.main import Test
from core.utils.time import parse_duration


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
            "Couldn't find units for last time quantity "
            "`23`. A valid duration is written with no spaces, and alternates between "
            'numbers and units of time (e.g. "2d1h5s").',
        )
        self.assert_equal(
            parse_duration("23g", ref),
            "Found character `g` which isn't a valid unit"
            ' of time. The options are "y", "n" (month), "d", "h", "m", "s".',
        )
