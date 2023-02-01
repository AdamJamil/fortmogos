import asyncio
import atexit
from collections import defaultdict
import os
import pickle
import attr
from datetime import datetime as dt, time as Time, timedelta
from dateutil.relativedelta import relativedelta
from typing import TYPE_CHECKING, DefaultDict, Dict, List, Optional, Tuple, TypeVar, Union

import discord


if TYPE_CHECKING:
    from discord.message import Message

start = dt.now()
speed_factor = 1000

def now() -> dt:
    if speed_factor == 1:
        return dt.now()
    return start + speed_factor * (dt.now() - start)


TOKEN = "MTA2MTcxOTY4Mjc3MzY4ODM5MQ.G16GQB.kUH5DsS4MAuqcOMDWAy9TwqSly5FpRjHjMOiC8"
GUILD = "suspcious"

client = discord.Client(intents=discord.Intents.all())

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


def parse_duration(duration_string: str, curr_time: dt) -> Union[dt, str]:
    valid_fmts = 'A valid duration is written with no spaces, and alternates between numbers and units of time (e.g. "2d1h5s").'
    ptr = 0
    time_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    while ptr < len(duration_string):
        cur = 0
        while ptr < len(duration_string) and duration_string[ptr].isnumeric():
            cur = 10 * cur + int(duration_string[ptr])
            ptr += 1
        if ptr == len(duration_string):
            return f"Couldn't find units for last time quantity `{cur}`. " + valid_fmts
        if duration_string[ptr] not in ['y', 'n', 'm', 'h', 'd', 's']:
            return (
                f'Found character `{duration_string[ptr]}` which isn\'t a valid unit of time. '
                'The options are "y", "n" (month), "d", "h", "m", "s".'
            )
        if duration_string[ptr] in time_map:
            curr_time += timedelta(seconds=cur) * time_map[duration_string[ptr]]
        elif duration_string[ptr] in ['n', 'y']:
            curr_time += relativedelta(months=cur * (12 if duration_string[ptr] == 'y' else 1))
        ptr += 1
    return curr_time


def parse_time(time_string: str) -> Union[Time, str]:
    valid_fmts = "The valid formats are HH{am/pm} and HH:MM{am/pm}."
    if (
        (":" in time_string and len(time_string) < 6 or len(time_string) > 7)
        or (":" not in time_string and len(time_string) < 3 or len(time_string) > 4)
    ):
        return f"`{time_string}` isn't formatted correctly. " + valid_fmts
    try:
        hour = int(time_string[0]) if len(time_string) % 3 == 0 else int(time_string[:2])
    except:
        if ":" in time_string:
            return f"Couldn't parse hour from `{time_string.split(':')[0]}`."
        return f"Couldn't parse hour from `{time_string[0]}`."

    if time_string[-2:].lower() not in ["am", "pm"]:
        return "Make sure the string ends in 'am' or 'pm'."
    hour = (hour % 12) + (12 * (time_string[-2].lower() == "p"))

    try:
        minute = int(time_string.split(":")[1][:2]) if len(time_string) > 4 else 0
    except:
        return f"Couldn't parse minute from `{time_string.split(':')[1][:2]}`."

    return Time(minute=minute, hour=hour)

def _date_suffix(day: int) -> str:
    date_suffix = ["th", "st", "nd", "rd"]

    if day % 10 in [1, 2, 3] and day not in [11, 12, 13]:
        return date_suffix[day % 10]
    else:
        return date_suffix[0]
    

def logical_time_repr(stamp: Union[dt, Time]) -> str:
    return stamp.strftime("%#I%p") if not stamp.minute else stamp.strftime("%#I:%M%p")


def logical_dt_repr(stamp: Union[dt, Time]) -> str:
    curr = now()
    if isinstance(stamp, Time):
        stamp = curr.replace(hour=stamp.hour, minute=stamp.minute, second=stamp.second)
    if stamp.year != curr.year:
        return stamp.strftime("on %#m/%#d/%y") + " at " + logical_time_repr(stamp)
    if stamp.month != curr.month:
        return stamp.strftime(f"on %b %#d{_date_suffix(int(stamp.strftime('%d')))}") + " at " + logical_time_repr(stamp)
    if stamp.day != curr.day:
        return stamp.strftime(f"on the %#d{_date_suffix(int(stamp.strftime('%d')))}") + " at " + logical_time_repr(stamp)
    return "at " + logical_time_repr(stamp)


def relative_day_str(stamp: Union[dt, Time]) -> str:
    curr = now()
    if isinstance(stamp, Time):
        return "Today"
    tomorrow = curr + relativedelta(days=1)
    if stamp.day == tomorrow.day and stamp.month == tomorrow.month and stamp.year == tomorrow.year:
        return "Tomorrow"
    if stamp.year != curr.year:
        return stamp.strftime("%#m/%#d/%y")
    if stamp.month != curr.month:
        return stamp.strftime(f"%b %#d{_date_suffix(int(stamp.strftime('%d')))}")
    if stamp.day != curr.day:
        return stamp.strftime(f"%#d{_date_suffix(int(stamp.strftime('%d')))}")
    return "Today"


T = TypeVar('T', bound=Union[dt, Time])


def replace_down(dest_stamp: T, idx: Union[int, str], source_stamp: Optional[Union[dt, Time]] = None, zero: bool = False) -> T:
    if not source_stamp and not zero:
        raise TypeError("fuck you")
    res = dest_stamp
    idx_to_attr: Dict[int, str] = {6: "year", 5: "month", 4: "day", 3: "hour", 2: "minute", 1: "second", 0: "microsecond"}
    if isinstance(idx, str):
        idx = {v: k for (k, v) in idx_to_attr.items()}[idx]
    dt_only = ["year", "month", "day"]
    for i in range(idx, -1, -1):
        attr = idx_to_attr[i]
        if attr in dt_only and not (isinstance(source_stamp, dt) and isinstance(dest_stamp, dt)):
            raise TypeError(f"requested {attr} from Time object")
        res = res.replace(**{attr: 0 if zero else getattr(source_stamp, attr)})
    
    return res

def get_day_to_reminders() -> DefaultDict[dt, List[Tuple[dt, "Alert"]]]:
    curr_time = now()
    day_to_reminders: DefaultDict[dt, List[Tuple[dt, Alert]]] = defaultdict(lambda: [])
    for reminder in data.tasks:
        reminder_day = replace_down(reminder_dt := reminder.get_next_activation(curr_time), 3, zero=True)
        day_to_reminders[reminder_day].append((reminder_dt, reminder))
    for reminders in day_to_reminders.values():
        reminders.sort(key=lambda x: x[0])
    return day_to_reminders

def list_reminders() -> str:
    day_to_reminders = get_day_to_reminders()
    ret = ""
    for day, reminders in day_to_reminders.items():
        ret += f"{relative_day_str(day)}\n" + "\n".join(
            f"  {logical_time_repr(reminder_time) + (' ' + reminder.descriptor_tag()).rstrip()}: {reminder.msg}"
            for reminder_time, reminder in reminders
        ) + "\n"
    return ret


class PersistentInfo():
    def __init__(self) -> None:
        self.tasks: List[Alert] = []
        self.alert_channels: List[discord.abc.MessageableChannel] = []

        if os.path.exists("data"):
            with open("data", "rb") as f:
                self.__dict__ = pickle.load(f).__dict__
                self.alert_channels = [
                    *map(client.get_partial_messageable, self.alert_channels_ids)
                ]

    def save(self) -> None:
        self.alert_channels_ids = [channel.id for channel in self.alert_channels]
        delattr(self, "alert_channels")
        with open("data", "wb") as f:
            pickle.dump(self, f)


@attr.s(auto_attribs=True)
class Alert:
    """Parent class of all alerts"""
    msg: str
    user: int
    channel_id: int
    _last_activated: dt = attr.field(init=False, default=now() - timedelta(days=100))
    _reminder_str: str = attr.field(init=False, default='Hey <@{user}>, this is a reminder to {msg}. It\'s currently {x}')
    repeats: bool = attr.field(init=False, default=True)

    def five_m_past_activation(self, curr_time: dt) -> bool:
        """Return true iff it's within five minutes of activation"""
        return False

    def should_activate(self, curr_time: dt) -> bool:
        return (
            curr_time - self._last_activated >= timedelta(hours=12) 
            and self.five_m_past_activation(curr_time)
        )

    async def activate(self) -> None:
        await client.get_partial_messageable(
            self.channel_id,
        ).send(self._reminder_str.format(user=self.user, msg=self.msg, x=now()))

    async def maybe_activate(self, curr_time: dt) -> bool:
        if (activated := self.should_activate(curr_time)):
            await self.activate()
            self._last_activated = now()
        return activated
    
    def get_next_activation(self, curr_time: dt) -> dt:
        raise NotImplementedError(f"class {type(self)} doesn't have get_next_activation implemented.")
    
    def descriptor_tag(self) -> str:
        raise NotImplementedError(f"class {type(self)} doesn't have descriptor_tag implemented.")


@attr.s(auto_attribs=True)
class DailyAlert(Alert):
    """Alerts that go off once a day"""
    alert_time: Time

    def five_m_past_activation(self, curr_time: dt) -> bool:
        """Return true iff it's within five minutes of activation"""
        return 0 <= time_dist(self.alert_time, curr_time.time()).total_seconds() <= 60 * 60
    
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


class Timer:
    def __init__(self):
        self.timer = now()

    async def run(self):
        if data.alert_channels:
            await asyncio.gather(*(channel.send("nyooooom") for channel in data.alert_channels))
        while 1:
            print(f"It's currently {' '.join(str(now()).split(' ')[1:])}")
            new_tasks: List[Alert] = []
            for task in data.tasks:
                if not await task.maybe_activate(self.timer) or task.repeats:
                    new_tasks.append(task)
            data.tasks = new_tasks

            await asyncio.sleep(max(0, .01 - (now() - self.timer).total_seconds()))
            self.timer = now()


@client.event
async def on_ready():
    guild = None
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    if guild is None:
        print("No guild detected.")
        return

    print(
        f"{client.user} is connected to the following guild:\n"
        f"{guild.name}(id: {guild.id})"
    )


help_messages = []

timer = Timer()
data = PersistentInfo()

@atexit.register
def shutdown():
    print(data.alert_channels)
    if data.alert_channels:
        # loop = asyncio.new_event_loop()
        print(data.alert_channels)
        loop.run_until_complete(
            asyncio.gather(*(channel.send("zzz") for channel in data.alert_channels))
        )
    data.save()


@client.event
async def on_message(msg: 'Message'):
    if msg.author.id == 1061719682773688391:
        return
    if msg.content.startswith("help "):
        print(dir(msg))
        print(type(msg.author), dir(msg.author), msg.author.id)
        if msg.content.endswith("reminder"):
            response = await msg.reply(
                f"Sure, <@{msg.author.id}>. Here are the options:\n"
                "```\n"
                    '\tin {duration} {msg} - e.g. "in 2d10h go play among us"\n'

                    '\ton {day} {msg} - e.g. "on friday go play among us"\n'
                    '\t                      "on 3/17 go play among us"\n'

                    '\tdaily {time} {msg} - e.g. "daily 9am get out of bed idiot"\n'

                    '\tweekly {day} {time} {msg} - '
                    'e.g. "weekly friday 6pm gamine time"\n'

                    '\tmonthly {day} {time} {msg} - '
                    'e.g. "monthly 20 9am pay rent"\n'

                    '\tmultiweekly {days} {time} {msg} - '
                    'e.g. "multiweekly [monday, wednesday] 10pm among us session"\n'
                    '\t                                  '
                    '     "multiweekly [monday-friday] 10am work time"\n'

                    '\tperiodic {frequency} {offset} {time} {msg} - '
                    'e.g. "periodic 14 3 7pm take recycling out biweekly"\n'
                    '\t                                             '
                    'The offset indicates how many days until the first reminder.\n'

                    '\trotation periodic {frequency} {offset} {time} {rotations} {msg} - '
                    'e.g. "rotation periodic 7 2 8am [impostor, crewmate] go take out trash"\n'

                    '\trotation multiweekly {days} {offset} {time} {rotations} {msg} - '
                    'e.g. "rotation multiweekly [wednesday, saturday] '
                    '2 8am [impostor, crewmate] go take out trash"\n'
                "```\n"
                'You can ask for any further help with "help reminder {name}" - '
                'e.g. "help reminder on". Also, this message will self-destruct shortly.'
            )
        await msg.delete()
    elif msg.content.startswith("daily "):
        tokens = [x for x in msg.content.split(" ") if x]
        time_str, reminder_str = tokens[1], " ".join(tokens[2:])
        if isinstance((reminder_time := parse_time(time_str)), str):
            response = msg.reply(
                f"Fuck you, <@{msg.author.id}>! Your command `{msg.content}` failed: {reminder_time}"
            )
        else:
            data.tasks.append(
                DailyAlert(reminder_str, msg.author.id, msg.channel.id, reminder_time)
            )
            response = msg.reply(
                f'<@{msg.author.id}>\'s daily reminder {logical_dt_repr(reminder_time)} to "{reminder_str}" has been set.'
            )
        await response
        await msg.delete()
    elif msg.content.startswith("in "):
        tokens = [x for x in msg.content.split(" ") if x]
        duration_str, reminder_str = tokens[1], " ".join(tokens[2:])
        if isinstance((reminder_time := parse_duration(duration_str, now())), str):
            response = msg.reply(
                f"Fuck you, <@{msg.author.id}>! Your command `{msg.content}` failed: {reminder_time}"
            )
        else:
            data.tasks.append(
                SingleAlert(reminder_str, msg.author.id, msg.channel.id, reminder_time)
            )
            response = msg.reply(
                f'<@{msg.author.id}>\'s reminder {logical_dt_repr(reminder_time)} to "{reminder_str}" has been set.'
            )
        await response
        await msg.delete()
    elif msg.content == "subscribe alerts":
        await msg.reply(
            f"Got it, <@{msg.author.id}>. This channel will now be used to send alerts out regarding the state of the bot."
        )
        data.alert_channels.append(msg.channel)
        await msg.delete()
    elif msg.content in ["list reminders", "show reminders", "see reminders", "view reminders"]:
        shit = list_reminders()
        if shit:
            await msg.reply(
                f"Here are your reminders, <@{msg.author.id}>."
                + ("\n```\n" + shit + "\n```")
            )
        else:
            await msg.reply(
                f"You have no reminders, <@{msg.author.id}>."
            )
        await msg.delete()
    elif msg.content.startswith("delete"):
        idx = int(msg.content.split(" ")[1])
        shit = get_day_to_reminders()
        reminders: List[Alert] = [y[1] for x in shit.values() for y in x]
        if idx < 0 or idx >= len(reminders):
            await msg.reply("Hey <@{msg.author.id}>, you're an idiot :D")
        else:
            data.tasks.remove(reminders[idx])
            await msg.reply("Hey <@{msg.author.id}>, your alert was deleted.")
        await msg.delete()


loop = asyncio.get_event_loop() 
loop.run_until_complete(asyncio.gather(client.start(TOKEN), timer.run()))
