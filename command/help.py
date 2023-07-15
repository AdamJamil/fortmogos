import discord

from core.data.handler import DataHandler


async def help_reminder(msg: discord.message.Message, _: DataHandler) -> None:
    await msg.reply(
        f"Sure, <@{msg.author.id}>. Here are the options:\n"
        "```\n"
        # in
        '\tin {duration} {msg} - e.g. "in 2d10h go play among us"\n'
        # on
        '\ton {day} {msg} - e.g. "on friday go play among us"\n'
        '\t                      "on 3/17 go play among us"\n'
        # daily
        '\tdaily {time} {msg} - e.g. "daily 9am get out of bed idiot"\n'
        # weekly
        "\tweekly {day} {time} {msg} - "
        'e.g. "weekly friday 6pm gamine time"\n'
        # monthly
        "\tmonthly {day} {time} {msg} - "
        'e.g. "monthly 20 9am pay rent"\n'
        # multiweekly
        "\tmultiweekly {days} {time} {msg} - "
        'e.g. "multiweekly [monday, wednesday] 10pm among us session"\n'
        "\t                                  "
        '     "multiweekly [monday-friday] 10am work time"\n'
        # periodic
        "\tperiodic {frequency} {offset} {time} {msg} - "
        'e.g. "periodic 14 3 7pm take recycling out biweekly"\n'
        "\t                                             "
        "The offset indicates how many days until the first reminder.\n"
        # rotation periodic
        "\trotation periodic {frequency} {offset} {time} {rotations} {msg} - "
        'e.g. "rotation periodic 7 2 8am [impostor, crewmate] go take out trash"\n'
        # rotation multiweekly
        "\trotation multiweekly {days} {offset} {time} {rotations} {msg} - "
        'e.g. "rotation multiweekly [wednesday, saturday] '
        '2 8am [impostor, crewmate] go take out trash"\n'
        "```\n"
        'You can ask for any further help with "help reminder {name}" - '
        'e.g. "help reminder on". Also, this message will self-destruct shortly.'
    )
    await msg.delete()
