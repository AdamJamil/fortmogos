from collections import defaultdict
from datetime import datetime as dt
from typing import (
    TYPE_CHECKING,
    DefaultDict,
    List,
    Tuple,
    cast,
)
from core.data.handler import DataHandler
from core.timer import now
from core.utils.time import logical_time_repr, relative_day_str, replace_down

if TYPE_CHECKING:
    from core.data.writable import Alert


def get_day_to_reminders(
    data: DataHandler,
    user_id: int,
) -> DefaultDict[dt, List[Tuple[dt, "Alert"]]]:
    from core.data.writable import Alert

    curr_time = now()
    day_to_reminders: DefaultDict[dt, List[Tuple[dt, Alert]]] = defaultdict(lambda: [])
    for reminder in data.tasks:
        if isinstance(reminder, Alert) and reminder.user == user_id:
            reminder_day = replace_down(
                reminder_dt := reminder.get_next_activation(curr_time), 3, zero=True
            )
            day_to_reminders[reminder_day].append((reminder_dt, reminder))
    for reminders in day_to_reminders.values():
        reminders.sort(key=lambda x: x[0])
    return day_to_reminders


def list_reminders(data: DataHandler, user_id: int) -> str:
    day_to_reminders = get_day_to_reminders(data, user_id)
    ret = ""
    for day, reminders in day_to_reminders.items():
        reminder_strs = (
            (
                "  "
                + logical_time_repr(reminder_time)
                + (" " + reminder.descriptor_tag).rstrip()
                + ": "
                + cast(str, reminder.msg)
            )
            for reminder_time, reminder in reminders
        )
        ret += f"{relative_day_str(day)}\n" + "\n".join(reminder_strs) + "\n"
    return ret
