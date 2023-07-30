from typing import Any, Dict, List
from unittest.mock import MagicMock, patch
from core.data.writable import AlertChannel
from disc.tests.main import Test
from core.start import data
from disc.tests.utils import MockChannel, user_says


def attrs(y: List[Any]) -> List[Dict[Any, Any]]:
    return [
        {
            k: getattr(x, k)
            for k in dir(x)
            if k != "_sa_instance_state"
            and not k.startswith("__")
            and hasattr(type(x), k)
            and (not type(x) is AlertChannel or k == "_id")
        }
        for x in y
    ]


class TestHandler(Test):
    def reload_data(self) -> None:
        object.__setattr__(data, "tasks", None)
        object.__setattr__(data, "alert_channels", None)
        object.__setattr__(data, "user_tasks", None)

        data.populate_data()

    def check_save_load(self) -> None:
        orig_tasks, orig_alerts = attrs(data.tasks), attrs(data.alert_channels)
        self.reload_data()
        new_tasks, new_alerts = attrs(data.tasks), attrs(data.alert_channels)
        self.assert_len(orig_tasks, len(new_tasks))
        self.assert_len(orig_alerts, len(new_alerts))
        for x, y in zip(sorted(orig_tasks, key=repr), sorted(new_tasks, key=repr)):
            self.assert_dict_equal(x, y)

    @patch("command.misc.client.get_channel")
    async def test_load(self, get_channel: MagicMock) -> None:
        get_channel.return_value = MockChannel(0)
        await user_says("in 3d8h5m4s wake up")
        self.check_save_load()

        await user_says("in 3d8h5m4s wake up")
        self.check_save_load()

        await user_says("daily 10am wake up")
        self.check_save_load()

        await user_says("subscribe alerts")
        self.check_save_load()
