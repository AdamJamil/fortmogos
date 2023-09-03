from __future__ import annotations

from typing import Union

from discord import Member, Reaction, User
from core.data.writable import UserTask
from core.utils.constants import todo_emoji


async def manage_reaction(reaction: Reaction, user: Union[User, Member]):
    from core.start import data

    msg = reaction.message
    if (alert := data.reminder_msgs.get((user.id, msg.content))) is not None:
        if str(reaction.emoji) == todo_emoji:
            await msg.reply(
                f"Got it, <@{user.id}>. Your reminder to {alert.msg} "
                "was added to your todo list."
            )
            data.user_tasks.append(UserTask(user.id, alert.msg))
