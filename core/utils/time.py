from datetime import datetime as dt, time as Time, timedelta
from typing import (
    Dict,
    Optional,
    TypeVar,
    Union,
)
from dateutil.relativedelta import relativedelta
import pytz
from pytz.tzinfo import BaseTzInfo
from core.timer import now


def parse_duration(
    duration_string: str,
    curr_time: dt,
) -> Union[dt, str]:
    """
    Takes in a UTC time and returns that time plus the duration in question.
    """
    valid_fmts = (
        "A valid duration is written with no spaces, and alternates "
        'between numbers and units of time (e.g. "2d1h5s").'
    )
    ptr = 0
    time_map = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    while ptr < len(duration_string):
        cur = 0
        while ptr < len(duration_string) and duration_string[ptr].isnumeric():
            cur = 10 * cur + int(duration_string[ptr])
            ptr += 1
        if ptr == len(duration_string):
            return f"Couldn't find units for last time quantity `{cur}`. " + valid_fmts
        if duration_string[ptr] not in ["y", "n", "m", "h", "d", "s"]:
            return (
                f"Found character `{duration_string[ptr]}` which "
                "isn't a valid unit of time. "
                'The options are "y", "n" (month), "d", "h", "m", "s".'
            )
        if duration_string[ptr] in time_map:
            curr_time += timedelta(seconds=cur) * time_map[duration_string[ptr]]
        elif duration_string[ptr] in ["n", "y"]:
            curr_time += relativedelta(
                months=cur * (12 if duration_string[ptr] == "y" else 1)
            )
        ptr += 1
    return curr_time


def parse_time(time_string: str, timezone: BaseTzInfo) -> Union[Time, str]:
    valid_fmts = "The valid formats are HH{am/pm} and HH:MM{am/pm}."
    if (":" in time_string and (len(time_string) < 6 or len(time_string) > 7)) or (
        ":" not in time_string and (len(time_string) < 3 or len(time_string) > 4)
    ):
        return f"`{time_string}` isn't formatted correctly. " + valid_fmts
    try:
        hour = (
            int(time_string[0]) if len(time_string) % 3 == 0 else int(time_string[:2])
        )
    except Exception:
        if ":" in time_string:
            return f"Couldn't parse hour from `{time_string.split(':')[0]}`."
        return f"Couldn't parse hour from `{time_string[0]}`."

    if time_string[-2:].lower() not in ["am", "pm"]:
        return "Make sure the string ends in 'am' or 'pm'."
    hour = (hour % 12) + (12 * (time_string[-2].lower() == "p"))

    try:
        minute = int(time_string.split(":")[1][:2]) if len(time_string) > 4 else 0
    except Exception:
        return f"Couldn't parse minute from `{time_string.split(':')[1][:2]}`."
    user_datetime = timezone.localize(
        now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    )
    return user_datetime.astimezone(pytz.utc).time()


def time_dist(t1: Time, t2: Time) -> timedelta:
    dt1 = dt(year=1, month=1, day=1, hour=t1.hour, minute=t1.minute, second=t1.second)
    dt2 = dt(year=1, month=1, day=1, hour=t2.hour, minute=t2.minute, second=t2.second)
    diff = dt2 - dt1
    if (s := diff.total_seconds()) < 0:
        # need to be careful of corner case, e.g. activates at 11:59, but
        # await hangs for a minute and so we need to check dist between
        # times 12:00 and 11:59. this accounts for that
        s += 24 * 60 * 60
    return timedelta(seconds=s)


def _date_suffix(day: int) -> str:
    date_suffix = ["th", "st", "nd", "rd"]

    if day % 10 in [1, 2, 3] and day not in [11, 12, 13]:
        return date_suffix[day % 10]
    else:
        return date_suffix[0]


def logical_time_repr(stamp: Union[dt, Time], timezone: BaseTzInfo) -> str:
    """
    Takes in a UTC timestamp and returns a string that represents the stamp in the
    user's timezone.
    """
    if isinstance(stamp, Time):
        stamp = replace_down(now(), "hour", stamp)
    stamp = stamp.astimezone(timezone)
    res = stamp.strftime("%I%p") if not stamp.minute else stamp.strftime("%I:%M%p")
    return res[res[0] == "0" :]


def logical_dt_repr(stamp: Union[dt, Time], timezone: BaseTzInfo) -> str:
    """
    stamp must be a UTC timestamp
    """
    curr = pytz.utc.localize(now())
    if isinstance(stamp, Time):
        stamp = curr.replace(hour=stamp.hour, minute=stamp.minute, second=stamp.second)
    if stamp.tzinfo is None:
        stamp = pytz.utc.localize(stamp)

    date_str = ""
    if stamp.year != curr.year:
        date_str = f'{stamp.strftime("on %#m/%#d/%y")}'
    elif stamp.month != curr.month:
        date_str = stamp.strftime(f"on %b %#d{_date_suffix(int(stamp.strftime('%d')))}")
    elif stamp.day != curr.day:
        date_str = stamp.strftime(
            f"on the %#d{_date_suffix(int(stamp.strftime('%d')))}"
        )
    return date_str + (" at " if date_str else "") + logical_time_repr(stamp, timezone)


def relative_day_str(stamp: Union[dt, Time], timezone: BaseTzInfo) -> str:
    curr = now().astimezone(timezone)
    if isinstance(stamp, Time):
        return "Today"
    tomorrow = curr + relativedelta(days=1)
    if (
        stamp.day == tomorrow.day
        and stamp.month == tomorrow.month
        and stamp.year == tomorrow.year
    ):
        return "Tomorrow"
    if stamp.year != curr.year:
        return stamp.strftime("%#m/%#d/%y")
    if stamp.month != curr.month:
        return stamp.strftime(f"%b %#d{_date_suffix(int(stamp.strftime('%d')))}")
    if stamp.day != curr.day:
        return stamp.strftime(f"%#d{_date_suffix(int(stamp.strftime('%d')))}")
    return "Today"


T = TypeVar("T", bound=Union[dt, Time])


def replace_down(
    dest_stamp: T,
    idx: Union[int, str],
    # replace fields in question from here
    source_stamp: Optional[Union[dt, Time]] = None,
    zero: bool = False,  # zero out the fields in question
) -> T:
    """
    Takes a destination timestamp to modify, a time unit, and a source timestamp to
    take values from (or alternatively just a zero flag). The time unit supplied will be
    the largest modified value in the destination timestamp. Everything smaller than
    this unit will also be modified.

    The destination timestamp is NOT directly modified. A copy is returned.
    """
    if not source_stamp and not zero:
        raise TypeError("fuck you")
    res = dest_stamp.replace()  # make a copy
    idx_to_attr: Dict[int, str] = {
        6: "year",
        5: "month",
        4: "day",
        3: "hour",
        2: "minute",
        1: "second",
        0: "microsecond",
    }
    if isinstance(idx, str):
        idx = {v: k for (k, v) in idx_to_attr.items()}[idx]
    dt_only = ["year", "month", "day"]
    for i in range(idx, -1, -1):
        attr = idx_to_attr[i]
        if attr in dt_only and not (
            isinstance(source_stamp, dt) and isinstance(dest_stamp, dt)
        ):
            raise TypeError(f"requested {attr} from Time object")
        res = res.replace(**{attr: 0 if zero else getattr(source_stamp, attr)})

    return res
