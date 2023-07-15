from __future__ import annotations

from typing import Union, cast

from discord import Member, Reaction, User
from core.data.handler import DataHandler
from core.data.writable import UserTask
from core.utils.constants import todo_emoji


async def manage_reaction(
    reaction: Reaction, user: Union[User, Member], data: DataHandler
):
    msg = reaction.message
    if (alert := data.reminder_msgs.get((user.id, msg))) is not None:
        if str(reaction.emoji) == todo_emoji:
            await msg.reply(
                f"Got it, <@{user.id}>. Your reminder to {alert.msg} "
                "was added to your todo list."
            )
            data.user_tasks.append(UserTask(user.id, cast(str, alert.msg)))
