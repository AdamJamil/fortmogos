from abc import abstractmethod
from datetime import datetime as dt, timedelta, time as Time
from math import ceil
from typing import Any, Dict, cast

import discord
import pytz
from core.timer import now
from core.utils.exceptions import MissingTimezoneException
from core.utils.time import logical_dt_repr, logical_time_repr, replace_down, time_dist
from core.utils.constants import client, todo_emoji
from sqlalchemy import Boolean, Column, Float, Integer, String
from sqlalchemy.orm import reconstructor  # type: ignore
from core.data.base import Base
from sqlalchemy.orm.attributes import InstrumentedAttribute

"""
NOTE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
If you ever need classes A <- B, where A and B both need to be saved to the db, you
need to define stuff like this:
    class AMixin(whatever):
    class A(AMixin, Base):
    class B(AMixin, Base):

You never want to inherit __tablename__ because it breaks shit.
"""


class Immutable:
    """
    DB-writable objects sometimes have two fields which correspond to the same data.
    These fields have to match each other, but it's error-prone if one field can be
    independently changed without the other changing. Therefore we make the classes
    immutable. Just make a copy of the object and pass in the updated info, so the
    necessary updates are automatically made.
    """

    def __setattr__(self, key: Any, value: Any) -> None:
        if hasattr(self, key) and not (
            hasattr(self.__class__, key)
            and isinstance(
                getattr(self.__class__, key),
                InstrumentedAttribute,
            )
        ):
            raise TypeError("Object is immutable - make a new copy instead.")
        super().__setattr__(key, value)


class Task(Immutable):
    """Represents any event that should occur in the future, possibly multiple times."""

    __abstract__ = True

    __id = Column(Integer, primary_key=True, autoincrement=True)

    def __init__(self) -> None:
        super(Task, self).__init__()
        self._activation_threshold = timedelta(seconds=30)
        self.repeatable = False

    @reconstructor
    def init_on_load(self) -> None:
        self._activation_threshold = timedelta(seconds=30)
        self.repeatable = False

    async def maybe_activate(self, curr_time: dt) -> bool:
        if activated := self.should_activate(curr_time):
            await self.activate()
        return activated

    @abstractmethod
    def should_activate(self, curr_time: dt) -> bool:
        ...

    @abstractmethod
    async def activate(self) -> None:
        ...

    @abstractmethod
    def get_next_activation(self, curr_time: dt) -> dt:
        ...

    @abstractmethod
    def soon_past_activation(self, curr_time: dt) -> bool:
        ...


class RepeatableTask(Task):
    """
    Base class for any task which repeats.
    """

    __abstract__ = True

    def __init__(self) -> None:
        super(RepeatableTask, self).__init__()
        self._repeat_activation_threshold = timedelta(seconds=60)
        self._last_activated = now() - timedelta(days=100)
        object.__setattr__(self, "repeatable", True)

    @reconstructor
    def init_on_load(self) -> None:
        super().init_on_load()
        self._repeat_activation_threshold = timedelta(seconds=60)
        self._last_activated = now() - timedelta(days=100)
        object.__setattr__(self, "repeatable", True)

    async def maybe_activate(self, curr_time: dt) -> bool:
        if activated := await Task.maybe_activate(self, curr_time):
            object.__setattr__(self, "_last_activated", curr_time)
        return activated

    def should_activate(self, curr_time: dt) -> bool:
        return (
            self.soon_past_activation(curr_time)
            and curr_time - self._last_activated > self._repeat_activation_threshold
        )


class PeriodicTask(RepeatableTask):
    """
    Inherit this class to add property of being triggered periodically.
    """

    __abstract__ = True

    _periodicity = Column(Float(40))
    _first_activation = Column(Float(40))

    def __init__(
        self,
        periodicity: timedelta,
        first_activation: dt,
        **kwargs: Dict[str, Any],
    ) -> None:
        super().__init__(**kwargs)
        self.periodicity = periodicity
        self._periodicity = periodicity.total_seconds()
        self.first_activation = first_activation
        self._first_activation = first_activation.timestamp()

    @reconstructor
    def init_on_load(self) -> None:
        super().init_on_load()
        self.periodicity = timedelta(seconds=self._periodicity)  # type: ignore
        self.first_activation = dt.fromtimestamp(
            self._first_activation, tz=None  # type: ignore
        )

    def get_next_activation(self, curr_time: dt) -> dt:
        # s + x * p >= c
        # x >= (c - s) / p
        repeats = ceil(
            (curr_time - self.first_activation + timedelta(milliseconds=500))
            / self.periodicity
        )
        return self.first_activation + repeats * self.periodicity

    def soon_past_activation(self, curr_time: dt) -> bool:
        next_activation = self.get_next_activation(curr_time)
        prev_activation = next_activation - self.periodicity
        return (
            timedelta()
            <= time_dist(prev_activation.time(), curr_time.time())
            <= self._activation_threshold
        )


class SingleTask(Task):
    """
    Inherit this class to add property of being triggered periodically.
    """

    __abstract__ = True

    _activation = Column[float](Float)

    def __init__(self, activation: dt) -> None:
        super(SingleTask, self).__init__()
        self.activation = activation
        self._activation = activation.timestamp()

    @reconstructor
    def init_on_load(self) -> None:
        super().init_on_load()
        self.activation = dt.fromtimestamp(self._activation)  # type: ignore

    def get_next_activation(self, curr_time: dt) -> dt:
        return self.activation

    def soon_past_activation(self, curr_time: dt) -> bool:
        return (
            timedelta() <= (curr_time - self.activation) <= self._activation_threshold
        )

    def should_activate(self, curr_time: dt) -> bool:
        return self.soon_past_activation(curr_time)


class Alert(Task):
    """Parent class of all alerts"""

    __abstract__ = True

    msg = Column(String)
    user = Column(Integer)
    channel_id = Column(Integer)
    descriptor_tag = Column(String)

    def __init__(
        self,
        msg: str,
        user: int,
        channel_id: int,
        descriptor_tag: str = "",
        **kwargs: Dict[Any, Any],
    ) -> None:
        super(Alert, self).__init__(**kwargs)
        self.msg = msg
        self.user = user
        self.channel_id = channel_id
        self.descriptor_tag = descriptor_tag
        self._reminder_str: str = (
            "Hey <@{user}>, this is a reminder to {msg}. It's currently {x}."
        )

    @reconstructor
    def init_on_load(self) -> None:
        super().init_on_load()
        self._reminder_str: str = (
            "Hey <@{user}>, this is a reminder to {msg}. It's currently {x}."
        )

    async def activate(self) -> None:
        """
        Just sends whatever message it's meant to send. Can be overridden by subclass
        e.g. for tasks we want to schedule for ourselves. May need to be refactored if
        we want to group alert messages together.
        """
        from core.bot import data

        try:
            msg = self._reminder_str.format(
                user=self.user,
                msg=self.msg,
                x=logical_dt_repr(now(), data.timezones[cast(int, self.user)].tz),
            )
        except MissingTimezoneException:
            msg = self._reminder_str.format(
                user=self.user,
                msg=self.msg,
                x="some unknown time, since we don't have your timezone.",
            )

        res = await client.get_partial_messageable(cast(int, self.channel_id)).send(msg)
        await res.add_reaction(todo_emoji)
        data.reminder_msgs[cast(int, self.user), res] = self

    @property
    @abstractmethod
    def full_desc(self) -> str:
        ...


class PeriodicAlert(Alert, PeriodicTask, Base):
    """Sends an alert at some periodicity"""

    __tablename__ = "periodic_alert"

    def __init__(
        self,
        msg: str,
        user: int,
        channel_id: int,
        periodicity: timedelta,
        first_activation: dt,
        descriptor_tag: str = "",
    ) -> None:
        super(PeriodicAlert, self).__init__(
            msg=msg,
            user=user,
            channel_id=channel_id,
            descriptor_tag=descriptor_tag,
            periodicity=periodicity,  # type: ignore
            first_activation=first_activation,  # type: ignore
        )

    @reconstructor
    def init_on_load(self) -> None:
        super().init_on_load()

    @property
    def full_desc(self) -> str:
        from core.bot import data

        if (self.periodicity - timedelta(days=1)).total_seconds() <= 5:
            time_str = logical_time_repr(
                self.first_activation, data.timezones[cast(int, self.user)].tz
            )
            return f"your daily reminder at {time_str} to {self.msg}"

        if (self.periodicity - timedelta(days=7)).total_seconds() <= 5:
            time_str = logical_time_repr(
                self.first_activation, data.timezones[cast(int, self.user)].tz
            )
            return f"your weekly reminder at {time_str} to {self.msg}"

        raise NotImplementedError(f"The periodicity {self.periodicity} is unknown.")


class SingleAlert(Alert, SingleTask, Base):
    """Sends only a single alert"""

    __tablename__ = "single_alert"

    def __init__(
        self,
        msg: str,
        user: int,
        channel_id: int,
        activation: dt,
        descriptor_tag: str = "",
    ) -> None:
        super(SingleAlert, self).__init__(
            msg=msg,
            user=user,
            channel_id=channel_id,
            descriptor_tag=descriptor_tag,
            activation=activation,  # type: ignore
        )

    @reconstructor
    def init_on_load(self) -> None:
        super().init_on_load()

    @property
    def full_desc(self) -> str:
        from core.bot import data

        time_str = logical_dt_repr(
            self.activation, data.timezones[cast(int, self.user)].tz
        )
        return f"your reminder at {time_str} to {self.msg}"


class AlertChannel(Base, discord.TextChannel):
    """
    Represents a messagable channel that should get bot alerts.
    The TextChannel subclass is hacky, but makes it type like a MessageableChannel.
    """

    __tablename__ = "alert_channel"

    _id = Column(Integer, primary_key=True)

    def __init__(
        self,
        channel: "discord.abc.MessageableChannel",
    ) -> None:
        self.set_channel(channel)
        self._id = channel.id

    @reconstructor
    def init_on_load(self) -> None:
        self.set_channel(client.get_channel(self._id))  # type: ignore

    def set_channel(self, channel: "discord.abc.MessageableChannel") -> None:
        for k in dir(channel):
            if k.startswith("__"):
                continue
            try:
                self.__setattr__(k, getattr(channel, k))
            except Exception:
                ...


class Timezone(Base):
    """
    Represents the timezone of a single user.
    """

    __tablename__ = "timezone"

    _id = Column(Integer, primary_key=True)
    _tz = Column(String)

    def __init__(self, user_id: int, tz: str) -> None:
        self._id = user_id
        self._tz = tz
        self.tz = pytz.timezone(self._tz)

    @reconstructor
    def init_on_load(self) -> None:
        self.tz = pytz.timezone(cast(str, self._tz))


class UserTask(Base):
    """
    A self-described user task. Appears in todo list.
    """

    __tablename__ = "user_task"

    _id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    desc = Column(String)
    completed = Column(Boolean)

    def __init__(self, user_id: int, desc: str):
        self.user_id = user_id
        self.desc = desc
        self.completed = False


class Wakeup(RepeatableTask, Base):
    """
    When the user wants to see their todo list.
    """

    __tablename__ = "wakeup"

    user = Column(Integer)
    _time = Column(Integer)
    channel = Column(Integer)
    disabled = Column(Boolean)

    def __init__(
        self, user: int, wakeup_time: Time, channel: int, disabled: bool = False
    ) -> None:
        super(Wakeup, self).__init__()
        self.user = user
        self.time = wakeup_time
        self._time = wakeup_time.hour * 3600 + wakeup_time.minute * 60
        self.channel = channel
        self.disabled = disabled

    @reconstructor
    def init_on_load(self) -> None:
        super(Wakeup, self).init_on_load()
        self.time = Time(
            hour=cast(int, self._time) // 3600, minute=cast(int, self._time) % 60
        )

    async def activate(self) -> None:
        if cast(bool, self.disabled):
            return

        from core.bot import data

        todo_str = "\n".join(
            f"{i+1}) {cast(str, y.desc)}"
            for i, y in enumerate(
                x for x in data.user_tasks if cast(int, x.user_id) == self.user
            )
        )

        if todo_str:
            await client.get_partial_messageable(cast(int, self.channel)).send(
                f"Good morning, <@{self.user}>! Here is your current todo list:\n```\n"
                + todo_str
                + "\n```"
            )

    def get_next_activation(self, curr_time: dt) -> dt:
        res = replace_down(curr_time, "hour", self.time)
        if res + self._activation_threshold < curr_time:
            res += timedelta(days=1)
        return res

    def soon_past_activation(self, curr_time: dt) -> bool:
        next_activation = self.get_next_activation(curr_time)
        prev_activation = next_activation - timedelta(days=1)
        return (
            timedelta()
            <= time_dist(prev_activation.time(), curr_time.time())
            <= self._activation_threshold
        )
