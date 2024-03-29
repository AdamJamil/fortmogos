from typing import Any, Dict, List
from disc.tests.main import Test
from core.start import data
from disc.tests.utils import user_says


def attrs(y: List[Any]) -> List[Dict[Any, Any]]:
    return [
        {
            k: getattr(x, k)
            for k in dir(x)
            if k != "_sa_instance_state"
            and not k.startswith("__")
            and hasattr(type(x), k)
            and k == "_id"
        }
        for x in y
    ]


class TestHandler(Test):
    def reload_data(self) -> None:
        object.__delattr__(data, "tasks")
        object.__delattr__(data, "user_tasks")
        object.__delattr__(data, "timezones")
        object.__delattr__(data, "wakeup")

        data.populate_data()

    def check_save_load(self) -> None:
        orig_tasks = attrs(data.tasks)
        self.reload_data()
        new_tasks = attrs(data.tasks)
        self.assert_len(orig_tasks, len(new_tasks))
        for x, y in zip(sorted(orig_tasks, key=repr), sorted(new_tasks, key=repr)):
            self.assert_dict_equal(x, y)

    async def test_load(self) -> None:
        await user_says("in 3d8h5m4s wake up")
        self.check_save_load()

        await user_says("in 3d8h5m4s wake up")
        self.check_save_load()

        await user_says("daily 10am wake up")
        self.check_save_load()

        await user_says("subscribe alerts")
        self.check_save_load()
