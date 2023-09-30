from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
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

from typing_extensions import TypeVarTuple, Unpack
from datetime import datetime as dt, time as Time

import pytz
from pytz import BaseTzInfo
from pytz import utc
from core.context import Context
from core.data.handler import DataHandler
from core.timer import now
from core.utils.time import parse_duration, replace_down


ARGS = TypeVarTuple("ARGS")
T1 = TypeVar("T1")
T2 = TypeVar("T2")
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
        | Callable[[Context, DataHandler, Unpack[ARGS]], RES],
    ) -> (
        Chain[Unpack[ARGS]]
        | Chain[Unpack[ARGS], T1]
        | Chain[Unpack[ARGS], T1, T2]
        | Command[Unpack[ARGS]]
    ):
        res: (
            Chain[Unpack[ARGS]]
            | Chain[Unpack[ARGS], T1]
            | Chain[Unpack[ARGS], T1, T2]
            | Command[Unpack[ARGS]]
        )
        if isinstance(o, Expr0):
            res = Chain[Unpack[ARGS]](self.exprs + [o])
        elif isinstance(o, Expr1):
            res = Chain[Unpack[ARGS], T1](self.exprs + [o])
        elif isinstance(o, Expr2):
            res = Chain[Unpack[ARGS], T1, T2](self.exprs + [o])
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


class Warn(str):
    ...


class Literal(Expr0):
    def __init__(self, *_val: str | Sequence[str]) -> None:
        super().__init__()
        val: List[List[str]] = [
            [chunk.lower()] if isinstance(chunk, str) else [x.lower() for x in chunk]
            for chunk in _val
        ]
        self.options: List[str] = [" ".join(choice) for choice in product(*val)]

    def match_word(
        self, x: Deque[str], actual: str, expect: str
    ) -> Tuple[()] | Warn | None:
        """Matches a single word from expected/actual strings."""
        if edit_distance_one(actual, expect):
            x.popleft()
            return Warn(f"Did you mean `{expect}` instead of `{actual}`?")
        return () if actual == expect and x.popleft() else None

    def match_option(self, option: str, x: Deque[str]) -> Tuple[()] | List[Warn] | None:
        """Matches an entire phrase."""
        tokens = option.split(" ")
        initial_tokens = len(x)
        warnings: List[Warn] = []
        for actual, expect in zip(tuple(x), tokens):
            actual = actual.lower()
            if isinstance(match := self.match_word(x, actual, expect), Warn):
                warnings.append(match)
            elif match is None:
                return None
        if initial_tokens < len(tokens):
            return None if warnings else [Warn("Ran out of tokens while parsing.")]
        return warnings or ()

    def match(self, x: Deque[str]) -> Tuple[()] | List[Warn] | None:
        """Tries all options"""
        best, dq_pop = min(
            (
                (self.match_option(option, xc := deque(x)), len(x) - len(xc))
                for option in self.options
            ),
            key=lambda x: res_key(x[0]),
        )
        for _ in range(dq_pop):
            x.popleft()
        return best

    def __repr__(self) -> str:
        return f"Literal({self.options})"


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
    def match_option(
        self,
        x: Deque[str],
        opt: Chain[Time],
    ) -> Tuple[Time] | List[Warn] | None:
        res: Tuple[Any, ...] = ()
        warnings: List[Warn] = []
        for expr in opt.exprs:
            curr = expr.match(x)
            if curr is None:
                return None
            elif isinstance(curr, List):
                warnings += curr
            else:
                res += curr
        return warnings or cast(Tuple[Time], res)

    def match(self, x: Deque[str]) -> Tuple[Time, str] | List[Warn] | None:
        """
        Gets a day and time of the week from an expression.
        Valid examples: Monday 2PM, 3:04AM saturday.
        """
        if len(x) == 1:
            return [Warn("Ran out of tokens while parsing.")]
        days = {
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        }
        options = chain.from_iterable(
            ((Literal(day) >> TimeExpr(), day), (TimeExpr() >> Literal(day), day))
            for day in days
        )
        best_time, best_day, dq_pop = min(
            (
                (
                    self.match_option(xc := deque(x), option[0]),
                    option[1],
                    len(x) - len(xc),
                )
                for option in options
            ),
            key=lambda x: res_key(x[0]),
        )
        for _ in range(dq_pop):
            x.popleft()
        if isinstance(best_time, tuple):
            return best_time[0], best_day
        return best_time

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
    def match_option(
        self,
        x: Deque[str],
        opt: Chain[int, Time] | Chain[Time, int],
    ) -> Tuple[Time, int] | Tuple[int, Time] | List[Warn] | None:
        res: Tuple[Any, ...] = ()
        warnings: List[Warn] = []
        for expr in opt.exprs:
            curr = expr.match(x)
            if curr is None:
                return None
            elif isinstance(curr, List):
                warnings += curr
            else:
                res += curr
        return warnings or cast(Tuple[Time, int] | Tuple[int, Time], res)

    def match(self, x: Deque[str]) -> Tuple[Time, int] | List[Warn] | None:
        """
        Gets a day and time of the month from an expression.
        Valid examples: 8AM 2nd, 3rd 9:21PM.
        """
        if len(x) == 1:
            return [Warn("Ran out of tokens while parsing.")]
        res, dq_pop = min(
            (
                (
                    self.match_option(xc := deque(x), option),
                    len(x) - len(xc),
                )
                for option in (
                    SuffixedNumExpr() >> TimeExpr(),
                    TimeExpr() >> SuffixedNumExpr(),
                )
            ),
            key=lambda x: res_key(x[0]),
        )
        for _ in range(dq_pop):
            x.popleft()
        if isinstance(res, tuple) and isinstance(res[0], int):
            res = cast(Tuple[Time, int], (res[1], res[0]))
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
        | Command[Any, Any, Any],
    ) -> None:
        self.commands = list(commands)

    def parse_message(self, msg: str) -> ParsedCommand:
        return min(
            (command.parse(msg) for command in self.commands),
            key=lambda parsed_command: res_key(parsed_command.res),
        )
