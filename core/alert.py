""""""

from datetime import datetime as dt, time as Time, timedelta
from dateutil.relativedelta import relativedelta
import attr
import discord
from core.timer import now


from core.utils import replace_down, time_dist


@attr.s(auto_attribs=True)
class Alert:
    """Parent class of all alerts"""

    msg: str
    user: int
    channel_id: int
    client: discord.Client
    _last_activated: dt = attr.field(init=False, default=now() - timedelta(days=100))
    _reminder_str: str = attr.field(
        init=False,
        default="Hey <@{user}>, this is a reminder to {msg}. It's currently {x}",
    )
    repeats: bool = attr.field(init=False, default=True)

    def five_m_past_activation(self, curr_time: dt) -> bool:
        """Return true iff it's within five minutes of activation"""
        return False

    def should_activate(self, curr_time: dt) -> bool:
        """
        Returns true if alert hasn't been set off too recently and we're within 5
        minutes of last activation.
        """
        return curr_time - self._last_activated >= timedelta(
            hours=12
        ) and self.five_m_past_activation(curr_time)

    async def activate(self) -> None:
        """
        Just sends whatever message it's meant to send. Can be overridden by subclass
        e.g. for tasks we want to schedule for ourselves. May need to be refactored if
        we want to group alert messages together.
        """
        await self.client.get_partial_messageable(
            self.channel_id,
        ).send(self._reminder_str.format(user=self.user, msg=self.msg, x=now()))

    async def maybe_activate(self, curr_time: dt) -> bool:
        if activated := self.should_activate(curr_time):
            await self.activate()
            self._last_activated = now()
        return activated

    def get_next_activation(self, curr_time: dt) -> dt:
        raise NotImplementedError(
            f"class {type(self)} doesn't have get_next_activation implemented."
        )

    def descriptor_tag(self) -> str:
        raise NotImplementedError(
            f"class {type(self)} doesn't have descriptor_tag implemented."
        )


@attr.s(auto_attribs=True)
class DailyAlert(Alert):
    """Alerts that go off once a day"""

    alert_time: Time

    def five_m_past_activation(self, curr_time: dt) -> bool:
        """Return true iff it's within five minutes of activation"""
        return (
            0 <= time_dist(self.alert_time, curr_time.time()).total_seconds() <= 60 * 60
        )

    def get_next_activation(self, curr_time: dt) -> dt:
        next_activation = replace_down(curr_time, "hour", source_stamp=self.alert_time)
        if next_activation < curr_time:
            next_activation += relativedelta(days=1)
        return next_activation

    def descriptor_tag(self) -> str:
        return "[daily]"


@attr.s(auto_attribs=True)
class SingleAlert(Alert):
    """Alerts that go off once"""

    alert_datetime: dt

    def five_m_past_activation(self, curr_time: dt) -> bool:
        """Return true iff it's within five minutes of activation"""
        return timedelta() <= curr_time - self.alert_datetime <= timedelta(minutes=60)

    def get_next_activation(self, curr_time: dt) -> dt:
        return self.alert_datetime

    def descriptor_tag(self) -> str:
        return ""
