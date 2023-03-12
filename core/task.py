from datetime import datetime as dt, timedelta
from math import ceil
from core.timer import now
from core.utils.time import time_dist
from core.utils.constants import client


class Task:
    """Represents any event that should occur in the future, possibly multiple times."""

    def __init__(self) -> None:
        self._activation_threshold = timedelta(seconds=30)
        self.repeatable = False

    async def maybe_activate(self, curr_time: dt) -> bool:
        if activated := self.should_activate(curr_time):
            await self.activate()
        return activated

    def should_activate(self, curr_time: dt) -> bool:
        raise NotImplementedError(
            f"class {type(self)} doesn't have should_activate implemented."
        )

    async def activate(self) -> None:
        raise NotImplementedError(
            f"class {type(self)} doesn't have activate implemented."
        )

    def get_next_activation(self, curr_time: dt) -> dt:
        raise NotImplementedError(
            f"class {type(self)} doesn't have get_next_activation implemented."
        )

    def soon_past_activation(self, curr_time: dt) -> bool:
        raise NotImplementedError(
            f"class {type(self)} doesn't have soon_past_activation implemented."
        )


class RepeatableTask(Task):
    """
    Base class for any task which repeats.
    """

    def __init__(self) -> None:
        super().__init__()
        self._repeat_activation_threshold = timedelta(seconds=30)
        self._last_activated = now() - timedelta(days=100)
        self.repeatable = True

    async def maybe_activate(self, curr_time: dt) -> bool:
        if activated := await Task.maybe_activate(self, curr_time):
            self._last_activated = now()
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

    def __init__(self, periodicity: timedelta, first_activation: dt) -> None:
        super().__init__()
        self.periodicity = periodicity
        self.first_activation = first_activation

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

    def __init__(self, activation: dt) -> None:
        super().__init__()
        self.activation = activation

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

    def __init__(
        self,
        msg: str,
        user: int,
        channel_id: int,
        descriptor_tag: str = "",
    ) -> None:
        Task.__init__(self)
        self.msg = msg
        self.user = user
        self.channel_id = channel_id
        self.descriptor_tag = descriptor_tag
        self._reminder_str: str = (
            "Hey <@{user}>, this is a reminder to {msg}. It's currently {x}"
        )

    async def activate(self) -> None:
        """
        Just sends whatever message it's meant to send. Can be overridden by subclass
        e.g. for tasks we want to schedule for ourselves. May need to be refactored if
        we want to group alert messages together.
        """
        await client.get_partial_messageable(
            self.channel_id,
        ).send(self._reminder_str.format(user=self.user, msg=self.msg, x=now()))


class PeriodicAlert(Alert, PeriodicTask):
    def __init__(
        self,
        msg: str,
        user: int,
        channel_id: int,
        periodicity: timedelta,
        first_activation: dt,
        descriptor_tag: str = "",
    ) -> None:
        Alert.__init__(self, msg, user, channel_id, descriptor_tag)
        PeriodicTask.__init__(self, periodicity, first_activation)


class SingleAlert(Alert, SingleTask):
    def __init__(
        self,
        msg: str,
        user: int,
        channel_id: int,
        activation: dt,
        descriptor_tag: str = "",
    ) -> None:
        Alert.__init__(self, msg, user, channel_id, descriptor_tag)
        SingleTask.__init__(self, activation)
