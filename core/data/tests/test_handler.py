from typing import Any, Dict, List
from core.utils.constants import get_test_channel
from tests.main import Test
from core.bot import data
from tests.utils import query_channel


def attrs(y: List[Any]) -> List[Dict[Any, Any]]:
    return [
        {
            k: getattr(x, k)
            for k in dir(x)
            if k != "_sa_instance_state"
            and not k.startswith("__")
            and hasattr(type(y), k)
        }
        for x in y
    ]


class TestHandler(Test):
    def reload_data(self) -> None:
        object.__setattr__(data, "tasks", None)
        object.__setattr__(data, "alert_channels", None)

        data.__init__(data.client)

    def check_save_load(self) -> None:
        orig_tasks, orig_alerts = attrs(data.tasks), attrs(data.alert_channels)
        self.reload_data()
        self.assert_equal(orig_tasks, attrs(data.tasks))
        self.assert_equal(orig_alerts, attrs(data.alert_channels))

    async def test_load(self) -> None:
        test_channel = get_test_channel()

        _ = await query_channel("in 3d8h5m4s wake up", test_channel)
        self.check_save_load()

        _ = await query_channel("in 3d8h5m4s wake up", test_channel)
        self.check_save_load()

        _ = await query_channel("daily 10am wake up", test_channel)
        self.check_save_load()

        _ = await query_channel("subscribe alerts", test_channel)
        self.check_save_load()
