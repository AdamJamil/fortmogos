from __future__ import annotations

from command.misc import hijack, respond_test
from core.context import Context
from core.utils.exceptions import MissingTimezoneException
from core.utils.parse import (
    NO_TZ,
    ArgParser,
    DurationExpr,
    KleeneStar,
    Literal,
    MonthlyTimeExpr,
    Num,
    TimeExpr,
    TimeZoneExpr,
    WeeklyTimeExpr,
)
from command.manage_wakeup import (
    change_wakeup_time,
    disable,
    enable,
    init_wakeup,
    set_channel,
)
from command.help import help_reminder
from command.manage_reminder import delete_reminder, show_reminders
from command.manage_task import add_task, delete_task, show_tasks
from command.manage_timezone import manage_timezone
from command.set_reminder import set_daily, set_in, set_monthly, set_weekly


SHOW = ("list", "show", "see", "view")
DELETE = ("delete", "remove")
TASKS = ("task", "tasks", "todo", "todos")
REMINDERS = ("reminder", "reminders")


class CommandProcessor:
    def __init__(self) -> None:
        self.arg_parser = ArgParser(
            NO_TZ() >> Literal("help reminder") >> help_reminder,
            NO_TZ() >> Literal("timezone") >> TimeZoneExpr() >> manage_timezone,
            NO_TZ() >> Literal("With a hey, ho") >> respond_test,
            Literal(SHOW, TASKS) >> show_tasks,
            Literal(DELETE, TASKS) >> Num() >> delete_task,
            Literal(SHOW, REMINDERS) >> show_reminders,
            Literal(DELETE, REMINDERS) >> Num() >> delete_reminder,
            Literal("exec") >> KleeneStar() >> hijack,
            Literal(TASKS) >> KleeneStar() >> add_task,
            Literal("wakeup disable") >> disable,
            Literal("wakeup enable") >> enable,
            Literal("wakeup set") >> set_channel,
            Literal("wakeup") >> TimeExpr() >> change_wakeup_time,
            Literal("daily") >> TimeExpr() >> KleeneStar() >> set_daily,
            Literal("weekly") >> WeeklyTimeExpr() >> KleeneStar() >> set_weekly,
            Literal("monthly") >> MonthlyTimeExpr() >> KleeneStar() >> set_monthly,
            Literal("in") >> DurationExpr() >> KleeneStar() >> set_in,
        )

    async def parse_and_respond(self, ctx: Context) -> None:
        from core.start import data

        parsed_command = self.arg_parser.parse_message(ctx.content())

        if parsed_command.needs_tz and not await ctx.is_timezone_set():
            raise MissingTimezoneException()

        if isinstance(parsed_command.res, list):  # warning
            await ctx.warn_message(parsed_command.res)
        elif isinstance(parsed_command.res, tuple):  # args
            await parsed_command.f(ctx, data, *parsed_command.res)

        if ctx.user_id not in data.wakeup and any(
            todo.user_id == ctx.user_id for todo in data.user_tasks
        ):
            await init_wakeup(ctx, data)
