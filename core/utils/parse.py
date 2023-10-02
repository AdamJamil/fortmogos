from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime as dt
from datetime import time as Time
from itertools import chain, product
from typing import (
    Any,
    Callable,
    Coroutine,
    Deque,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    cast,
    overload,
)

import pytz
from dateutil.relativedelta import relativedelta
from pytz import BaseTzInfo, utc
from typing_extensions import TypeVarTuple, Unpack

from core.context import Context
from core.data.handler import DataHandler
from core.timer import now
from core.utils.time import parse_duration, replace_down

ARGS = TypeVarTuple("ARGS")
T = TypeVar("T")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
RES = Coroutine[Any, Any, None]


def edit_distance_one(x: str, y: str) -> bool:
    if x == y:
        return False
    if len(x) == len(y) and sum(1 for c1, c2 in zip(x, y) if c1 != c2) == 1:
        return True
    if len(x) > len(y):
        x, y = y, x
    if len(x) + 1 == len(y):
        diff = 0
        while diff < len(x) and x[diff] == y[diff]:
            diff += 1
        if x[diff:] == y[diff + 1 :]:
            return True
    if len(x) == len(y):
        for i in range(len(x) - 1):
            if x[:i] + x[i + 1] + x[i] + x[i + 2 :] == y:
                return True
    return False


def almost_number(x: str) -> bool:
    return sum(1 for c in x if c.isnumeric()) == len(x) - 1


def res_key(res: List[Warn] | Tuple[Any, ...] | None) -> Tuple[float, int]:
    return (
        3
        if res is None
        else 1 + bool(res and str(res[0]).startswith("Ran out"))
        if isinstance(res, list)
        else 0,
        len(res) if isinstance(res, list) else 0,
    )


class Expr(ABC):
    @abstractmethod
    def match(self, x: Deque[str]) -> Tuple[Any, ...] | List[Warn] | None:
        ...


class Chain(Generic[Unpack[ARGS]]):
    exprs: List[Expr]
    f: Optional[Callable[[Context, DataHandler], RES]]
    needs_tz: bool = True

    def __init__(self, exprs: Optional[List[Expr]] = None) -> None:
        self.exprs: List[Expr] = exprs or []

    @overload
    def __rshift__(self, o: Expr0) -> Chain[Unpack[ARGS]]:
        ...

    @overload
    def __rshift__(self, o: Expr1[T1]) -> Chain[Unpack[ARGS], T1]:
        ...

    @overload
    def __rshift__(self, o: Expr2[T1, T2]) -> Chain[Unpack[ARGS], T1, T2]:
        ...

    @overload
    def __rshift__(self, o: Expr3[T1, T2, T3]) -> Chain[Unpack[ARGS], T1, T2, T3]:
        ...

    @overload
    def __rshift__(
        self,
        o: Callable[[Context, DataHandler, Unpack[ARGS]], RES],
    ) -> Command[Unpack[ARGS]]:
        ...

    def __rshift__(
        self,
        o: Expr0
        | Expr1[T1]
        | Expr2[T1, T2]
        | Expr3[T1, T2, T3]
        | Callable[[Context, DataHandler, Unpack[ARGS]], RES],
    ) -> (
        Chain[Unpack[ARGS]]
        | Chain[Unpack[ARGS], T1]
        | Chain[Unpack[ARGS], T1, T2]
        | Chain[Unpack[ARGS], T1, T2, T3]
        | Command[Unpack[ARGS]]
    ):
        res: (
            Chain[Unpack[ARGS]]
            | Chain[Unpack[ARGS], T1]
            | Chain[Unpack[ARGS], T1, T2]
            | Chain[Unpack[ARGS], T1, T2, T3]
            | Command[Unpack[ARGS]]
        )
        if isinstance(o, Expr0):
            res = Chain[Unpack[ARGS]](self.exprs + [o])
        elif isinstance(o, Expr1):
            res = Chain[Unpack[ARGS], T1](self.exprs + [o])
        elif isinstance(o, Expr2):
            res = Chain[Unpack[ARGS], T1, T2](self.exprs + [o])
        elif isinstance(o, Expr3):
            res = Chain[Unpack[ARGS], T1, T2, T3](self.exprs + [o])
        else:
            res = Command[Unpack[ARGS]](self.exprs, o, self.needs_tz)
        res.needs_tz = self.needs_tz
        return res


class NO_TZ(Chain[()]):
    def __init__(self, exprs: List[Expr] | None = None) -> None:
        self.exprs: List[Expr] = exprs or []

    needs_tz: bool = False


class Command(Generic[Unpack[ARGS]]):
    """Represents a completed command"""

    def __init__(
        self,
        exprs: List[Expr],
        f: Callable[[Context, DataHandler, Unpack[ARGS]], RES],
        needs_tz: bool,
    ) -> None:
        self.exprs = exprs
        self.f = f
        self.needs_tz = needs_tz

    def parse(self, msg: str) -> ParsedCommand:
        while "  " in msg:
            msg = msg.replace("  ", " ")
        dq = deque(msg.split(" "))
        args: List[Any] = []
        warnings: List[Warn] = []
        for expr in self.exprs:
            if not dq:
                warnings.append(Warn("Ran out of tokens while parsing."))
                break
            res = expr.match(dq)
            if isinstance(res, Warn):
                warnings.append(res)
            elif isinstance(res, tuple):
                args.extend(res)
            else:
                return ParsedCommand(self.f, self.needs_tz, None)
        if dq:
            warnings.append(Warn("Unexpected tokens after parsing."))
        return ParsedCommand(
            self.f,
            self.needs_tz,
            warnings or tuple(args),
        )

    def __repr__(self) -> str:
        return str(self.exprs)


class ParsedCommand:
    def __init__(
        self,
        f: Callable[..., RES],
        needs_tz: bool,
        res: List[Warn] | Tuple[Any, ...] | None,
    ) -> None:
        self.f = f
        self.needs_tz = needs_tz
        self.res = res

    def __str__(self) -> str:
        return f"Parsed to function {self.f.__name__}: {self.res}"


class Expr0(Expr, Chain[()]):
    def __init__(self) -> None:
        # calling super init kills mypy...
        self.exprs: List[Expr] = [self]

    @abstractmethod
    def match(self, x: Deque[str]) -> Tuple[()] | List[Warn] | None:
        ...


class Expr1(Chain[T1], Expr):
    def __init__(self) -> None:
        # calling super init kills mypy...
        self.exprs: List[Expr] = [self]

    @abstractmethod
    def match(self, x: Deque[str]) -> Tuple[T1] | List[Warn] | None:
        ...


class Expr2(Chain[T1, T2], Expr):
    def __init__(self) -> None:
        # calling super init kills mypy...
        self.exprs: List[Expr] = [self]

    @abstractmethod
    def match(self, x: Deque[str]) -> Tuple[T1, T2] | List[Warn] | None:
        ...


class Expr3(Chain[T1, T2, T3], Expr):
    def __init__(self) -> None:
        # calling super init kills mypy...
        self.exprs: List[Expr] = [self]

    @abstractmethod
    def match(self, x: Deque[str]) -> Tuple[T1, T2, T3] | List[Warn] | None:
        ...


class Warn(str):
    ...


class ExprGroup(Generic[T]):
    """
    The group matches if any list of exprs from expr_options matches.
    """

    def __init__(
        self, expr_options: List[List[Expr]], metadata: Optional[List[T]] = None
    ) -> None:
        self.expr_options = expr_options
        self.metadata = metadata

    def match(self, x: Deque[str]) -> Tuple[Tuple[Any, ...] | List[Warn] | None, T]:
        """
        Try all options out, pick best.
        """
        best, dq_pop, best_metadata = min(
            (
                (self.match_option(option, xc := deque(x)), len(x) - len(xc), metadata)
                for option, metadata in zip(
                    self.expr_options,
                    self.metadata or [cast(T, None)] * len(self.expr_options),
                )
            ),
            key=lambda x: res_key(x[0]),
        )
        for _ in range(dq_pop):
            x.popleft()
        return best, best_metadata

    def match_option(
        self, option: List[Expr], x: Deque[str]
    ) -> Tuple[Any, ...] | List[Warn] | None:
        """Try matching on an option of exprs"""
        res: Tuple[Any, ...] = ()
        warnings: List[Warn] = []
        for expr in option:
            if not len(x):
                return [Warn("Ran out of tokens while parsing.")]
            curr = expr.match(x)
            if curr is None:
                return None
            elif isinstance(curr, List):
                warnings += curr
            else:
                res += curr
        return warnings or res


class _SingleLiteral(Expr0):
    def __init__(self, word: str) -> None:
        super().__init__()
        self.word = word

    def match(self, x: Deque[str]) -> Tuple[()] | List[Warn] | None:
        """Matches a single word from expected/actual strings."""
        if not len(x):
            return [Warn("Ran out of tokens while parsing.")]
        if edit_distance_one(actual := x[0].lower(), self.word):
            x.popleft()
            return [Warn(f"Did you mean `{self.word}` instead of `{actual}`?")]
        return () if actual == self.word and x.popleft() else None

    def __repr__(self) -> str:
        return f"_SingleLiteral({self.word})"


class Literal(Expr0):
    def __init__(self, *_val: str | Sequence[str]) -> None:
        super().__init__()
        val: List[List[str]] = [
            [chunk.lower()] if isinstance(chunk, str) else [x.lower() for x in chunk]
            for chunk in _val
        ]
        strd_options = [list(choice) for choice in product(*val)]
        self.expr_group = ExprGroup[None](
            expr_options=[
                [
                    _SingleLiteral(word)
                    for phrase in option
                    for word in phrase.split(" ")
                ]
                for option in strd_options
            ]
        )

    def match(self, x: Deque[str]) -> Tuple[()] | List[Warn] | None:
        return cast(Tuple[()] | List[Warn] | None, self.expr_group.match(x)[0])

    def __repr__(self) -> str:
        return f"Literal({self.expr_group.expr_options})"


class Num(Expr1[int]):
    def match(self, x: Deque[str]) -> Tuple[int] | List[Warn] | None:
        if almost_number(x[0]):
            res = x.popleft()
            return [Warn(f"Expected number; got `{res}`.")]
        return (int(val),) if x and x[0].isnumeric() and (val := x.popleft()) else None

    def __repr__(self) -> str:
        return "Num"


class DurationExpr(Expr1[dt]):
    def match(self, x: Deque[str]) -> Tuple[dt] | List[Warn] | None:
        """
        Gets the longest prefix possible that matches a duration.
        """
        best = -1, now()
        curr = ""
        last_fail = False
        curr_time = best[1]
        for i in range(min(len(x), 16)):
            curr += x[i]
            if isinstance(duration := parse_duration(curr, curr_time), str):
                if last_fail:
                    break
                last_fail = True
            else:
                last_fail = False
                best = max(best, (i, duration))

        if best[0] == -1:
            first = x.popleft()
            if not first[0].isnumeric():
                return None
            if not first.isnumeric():  # this maybe has units; try to parse them
                return [Warn(parse_duration(first, curr_time))]
            # first is definitely a number now
            if not len(x):
                return [Warn(f"Didn't find a time unit after `{first}`")]
            # at least two tokens, first one is a number, second should've be a unit
            # (or more), however this must've failed as best is -1
            return [Warn(parse_duration(first + x.popleft(), curr_time))]

        for _ in range(best[0] + 1):  # consumed tokens
            x.popleft()
        return (best[1],)

    def __repr__(self) -> str:
        return "Duration"


class TimeExpr(Expr1[Time]):
    def match(self, x: Deque[str]) -> Tuple[Time] | List[Warn] | None:
        """
        Extracts a time from the message.
        Valid format examples: 4pm, 4 pm, 420pm, 420 pm, 4:20pm, 4:20 pm
        """
        first = x.popleft()
        if sum(1 for c in first if c == ":") > 1:
            return None
        first = first.replace(":", "")
        if not first:
            return None

        if first.isnumeric():
            num = first
            if not x:
                return [Warn("Ran out of tokens while parsing.")]
            time_sig = x.popleft().lower()  # am/pm
        else:
            if len(first) < 3:
                return None
            num = first[:-2]
            if not num.isnumeric():
                return None
            time_sig = first[-2:].lower()

        if len(num) > 4:
            return None

        hour = int(num) if len(num) <= 2 else int(num[:-2])
        minute = 0 if len(num) <= 2 else int(num[-2:])

        if hour > 12:
            return [Warn(f"Found invalid hour: {hour}")]
        if minute >= 60:
            return [Warn(f"Found invalid minute: {minute}")]
        if hour < 0 or minute < 0:
            return [Warn("wtf")]

        if time_sig not in ("am", "pm"):
            return [Warn(f"Expected time signature `am` or `pm`, found {time_sig}.")]

        hour = (hour % 12) + 12 * (time_sig == "pm")
        return (Time(hour=hour, minute=minute, second=0, microsecond=0),)

    def __repr__(self) -> str:
        return "Time"


class WeeklyTimeExpr(Expr2[Time, str]):
    """
    Gets a day and time of the week from an expression.
    Valid examples: Monday 2PM, 3:04AM saturday.
    """

    def __init__(self) -> None:
        days = {
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        }
        self.expr_group = ExprGroup[str](
            list(
                chain.from_iterable(
                    (
                        [_SingleLiteral(day), TimeExpr()],
                        [TimeExpr(), _SingleLiteral(day)],
                    )
                    for day in days
                )
            ),
            [day for day in days for _ in range(2)],
        )

    def match(self, x: Deque[str]) -> Tuple[Time, str] | List[Warn] | None:
        if len(x) == 1:
            return [Warn("Ran out of tokens while parsing.")]
        res, day = self.expr_group.match(x)
        if isinstance(res, tuple):
            return res[0], day
        return res

    def __repr__(self) -> str:
        return "WeekOffset"


class SuffixedNumExpr(Expr1[int]):
    def match(self, x: Deque[str]) -> Tuple[int] | List[Warn] | None:
        """
        Matches either a normal number or something like "3rd"
        """
        if x[0].isnumeric():
            return (int(x.popleft()),)
        if (
            len(x[0]) < 3
            or not x[0][:-2].isnumeric()
            or x[0][-2:] not in ("st", "nd", "rd", "th")
        ):
            return None
        return (int(x.popleft()[:-2]),)

    def __repr__(self) -> str:
        return "IndexedNum"


class MonthlyTimeExpr(Expr2[Time, int]):
    def __init__(self) -> None:
        self.expr_group = ExprGroup[None](
            [
                [SuffixedNumExpr(), TimeExpr()],
                [TimeExpr(), SuffixedNumExpr()],
            ],
        )

    def match(self, x: Deque[str]) -> Tuple[Time, int] | List[Warn] | None:
        """
        Gets a day and time of the month from an expression.
        Valid examples: 8AM 2nd, 3rd 9:21PM.
        """
        if len(x) == 1:
            return [Warn("Ran out of tokens while parsing.")]
        res, _ = self.expr_group.match(x)
        if isinstance(res, tuple) and isinstance(res[0], int):
            return cast(Tuple[Time, int], (res[1], res[0]))
        return cast(Tuple[Time, int] | List[Warn] | None, res)

    def __repr__(self) -> str:
        return "MonthlyTime"


class TimeZoneExpr(Expr1[BaseTzInfo]):
    most_common = [
        "US/Alaska",
        "US/Arizona",
        "US/Central",
        "US/Eastern",
        "US/Hawaii",
        "US/Mountain",
        "US/Pacific",
        "Asia/Shanghai",
        "Asia/Kolkata",
        "Asia/Tehran",
        "Asia/Tokyo",
        "Brazil/East",
        "Asia/Dhaka",
        "Asia/Jakarta",
        "Asia/Chongqing",
        "Africa/Lagos",
        "Asia/Manila",
        "Africa/Cairo",
        "Asia/Seoul",
        "Europe/Istanbul",
        "Europe/Moscow",
        "America/Mexico_City",
        "Europe/Paris",
        "Europe/London",
        "America/Bogota",
        "Asia/Karachi",
        "UTC",
    ]

    def match(self, x: Deque[str]) -> Tuple[BaseTzInfo] | List[Warn] | None:
        best: Tuple[float, Optional[BaseTzInfo]] = 10**20, None
        if x[0].startswith("UTC"):
            tz_str = x.popleft()
            try:
                offset = int(tz_str[3:])
            except TypeError:
                return [Warn(f"Could not parse offset {tz_str[3:]}.")]
            else:
                utc_now = pytz.utc.localize(now())

                def _check(
                    best: Tuple[float, Optional[BaseTzInfo]], tz_name: str
                ) -> Tuple[float, Optional[BaseTzInfo]]:
                    timezone = pytz.timezone(tz_name)
                    local_now = timezone.localize(utc_now.replace(tzinfo=None))
                    # utc - offset = local
                    # utc - local = offset
                    return min(
                        best,
                        (
                            abs(
                                (utc_now - local_now).total_seconds()
                                - (offset * 60 * 60)
                            ),
                            timezone,
                        ),
                        key=lambda x: x[0],
                    )

                for tz_name in (*TimeZoneExpr.most_common, *pytz.common_timezones):
                    best = _check(best, tz_name)
                    if best[0] < 20 * 60:
                        break
                return (
                    [Warn("Did not find any matching timezones.")]
                    if best[1] is None
                    else (best[1],)
                )
        elif isinstance(res := TimeExpr().match(xc := deque(x)), (tuple, list)):
            for _ in range(len(x) - len(xc)):
                x.popleft()
            if isinstance(res, tuple):
                _curr_time = res[0]
                utc_now = utc.localize(now())
                curr_time = replace_down(utc_now, "hour", _curr_time)

                def _check(
                    best: Tuple[float, Optional[BaseTzInfo]], tz_name: str
                ) -> Tuple[float, Optional[BaseTzInfo]]:
                    timezone = pytz.timezone(tz_name)
                    user_tz_guess = timezone.localize(curr_time.replace(tzinfo=None))
                    res = abs((user_tz_guess - utc_now).total_seconds()) % 86400
                    return min(
                        best,
                        (res, timezone),
                        key=lambda x: x[0],
                    )

                for tz_name in (*TimeZoneExpr.most_common, *pytz.common_timezones):
                    best = _check(best, tz_name)
                    if best[0] < 20 * 60:
                        break

                return (
                    [Warn("Did not find any matching timezones.")]
                    if best[1] is None
                    else (best[1],)
                )
            return res
        else:  # this is a region name
            tz_str = ""
            try:
                return (pytz.timezone(tz_str := x.popleft()),)
            except Exception:
                return [
                    Warn(
                        f"{tz_str} is not a valid region, UTC offset, or time. Try "
                        "Google to find your region name, which might look like "
                        '"US/Eastern", or try providing your local time or UTC offset.'
                    )
                ]

    def __repr__(self) -> str:
        return "TimeZone"


class _SlashedDateExpr(Expr1[relativedelta]):
    """
    Options:
        1) (if year=False) day/month
        2) (if year=True) day/month/year
    """

    def __init__(self, year: bool) -> None:
        self.year = year

    def match(self, x: Deque[str]) -> Tuple[relativedelta] | List[Warn] | None:
        if sum(1 for c in x[0] if c == "/") != 2 + self.year:
            return None
        date = x.popleft()
        if not all(x.isnumeric() for x in date.split("/")):
            return None
        month, day = map(int, date.split("/")[:2])

        try:
            if self.year:
                year = int(date.split("/")[-1])
                return (relativedelta(day=day, month=month, year=year),)
            return (relativedelta(day=day, month=month),)
        except Exception:
            return [Warn("Invalid date arguments.")]


class DateExprType:
    TODAY = 0
    TOMORROW = 1
    DAY_OF_MONTH = 2
    DAY_MONTH = 3
    DAY_MONTH_YEAR = 4


class DateExpr(Expr2[relativedelta, relativedelta | None]):
    """
    Options:
        1) today
        2) tomorrow
        3) {num}{positional suffix} (e.g. 9th)
        4) day/month (TODO: user preference for day/month or month/day
            (or determine from TZ??))
        5) day/month/year
        6) TODO: {month} {num}{positional suffix} (e.g. sept 6th)

    see "annoying casework" below
    """

    def __init__(self) -> None:
        self.expr_group = ExprGroup[int](
            [
                [_SingleLiteral("today")],
                [_SingleLiteral("tomorrow")],
                [SuffixedNumExpr()],
                [_SlashedDateExpr(year=False)],
                [_SlashedDateExpr(year=True)],
            ],
            [
                DateExprType.TODAY,
                DateExprType.TOMORROW,
                DateExprType.DAY_OF_MONTH,
                DateExprType.DAY_MONTH,
                DateExprType.DAY_MONTH_YEAR,
            ],
        )

    def match(
        self, x: Deque[str]
    ) -> Tuple[relativedelta, relativedelta | None] | List[Warn] | None:
        res, date_expr_type = self.expr_group.match(x)
        if isinstance(res, tuple):
            if date_expr_type == DateExprType.TODAY:
                return (relativedelta(), None)
            if date_expr_type == DateExprType.TOMORROW:
                return (relativedelta(days=1), None)
            if date_expr_type == DateExprType.DAY_OF_MONTH:
                return (relativedelta(day=res[0]), relativedelta(months=1))
            if date_expr_type == DateExprType.DAY_MONTH:
                return (res[0], relativedelta(years=1))
            if date_expr_type == DateExprType.DAY_MONTH_YEAR:
                return (res[0], None)
        return cast(List[Warn] | None, res)


class DateTimeExpr(Expr3[Time, relativedelta, relativedelta | None]):
    """
    Options:
        1) {time}  # surprise, you don't need a date
        2) {time} (on) {date}  # parens means optional word
        3) {date} (on) {time}  # don't care if user has shitty grammar

    annoying casework:
        1) time only
            *cannot* return dt with just now() replace_down'd with time
              this is because utc day might not match user day
            must return a Time
        2) time and "today"
            cannot return a dt. utc day can mismatch
            one option: Time + relativedelta()
        3) time and "tomorrow"
            same as above, but relativedelta(days=1)
        4) time and suffixed day
            if suffixed day + time is invalid =>
              we want to just add relativedelta(months=1)
            one option: return Time + relativedelta(day=, month=)
        5) time and M/D
            year might still mismatch
            can return same as above, but instead of month increment, year increment is
              what the user would expect..
        6) time and M/D/Y
            M/D/Y is absolute, so we can return a dt or convert that to whatever


        hypothesis: Time + relativedelta()
        1&2) without day, default to just "today", so 1 and 2 are same
            relativedelta()
            grab Time, grab user's now(), replace_down reminder time
            if invalid time, reminder should NOT be set
        3) time and "tomorrow"
            relativedelta(days=1)
            grab Time, grab user's now(), replace_down reminder time, add a day
            will definitely be in future, always valid
        4) time and suffixed day
            relativedelta(day=day)
            if invalid, add a month
        5) time and M/D
            relativedelta(day=day, month=month)
            if invalid, add a year
        6) time and M/D/Y
            relativedelta(day=day, month=month, year=year)

        OK, but need to add behavior for invalid (fail, or add certain delta)
            solution: add an optional adjustment
    """

    def __init__(self) -> None:
        self.expr_group = ExprGroup[None](
            [
                [TimeExpr()],
                [TimeExpr(), _SingleLiteral("on"), DateExpr()],
                [TimeExpr(), DateExpr()],
                [DateExpr(), _SingleLiteral("on"), TimeExpr()],
                [DateExpr(), TimeExpr()],
            ],
        )

    def match(
        self, x: Deque[str]
    ) -> Tuple[Time, relativedelta, relativedelta | None] | List[Warn] | None:
        res, _ = self.expr_group.match(x)
        if isinstance(res, tuple):
            if len(res) == 1:  # time only
                return (res[0], relativedelta(), None)  # fail if invalid time
            if not isinstance(res[0], Time):  # (rd, rd | None, Time)
                res = res[2], res[0], res[1]
        return cast(
            Tuple[Time, relativedelta, relativedelta | None] | List[Warn] | None, res
        )


class KleeneStar(Expr1[str]):
    def match(self, x: Deque[str]) -> Tuple[str] | List[Warn] | None:
        res = x.popleft()
        while x:
            res += " " + x.popleft()
        return (res,)

    def __repr__(self) -> str:
        return "KleeneStar"


class ArgParser:
    def __init__(
        self,
        *commands: Command[()]
        | Command[Any]
        | Command[Any, Any]
        | Command[Any, Any, Any]
        | Command[Any, Any, Any, Any],
    ) -> None:
        self.commands = list(commands)

    def parse_message(self, msg: str) -> ParsedCommand:
        return min(
            (command.parse(msg) for command in self.commands),
            key=lambda parsed_command: res_key(parsed_command.res),
        )
