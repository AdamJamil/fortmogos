import os
import discord


from custom_typing.protocols import Str_able

with open("token.txt", "r") as f:
    TOKEN, TEST_TOKEN, FAKE_TOKEN = f.read().strip().split("\n")


def get_token():
    """
    This function is mocked during testing.
    """
    return TOKEN


fakemogus_id = 1089042918259564564
testmogus_id = 0

client = discord.Client(intents=discord.Intents.all())

banned_users = {442721077408563200}


class Separator:
    """
    Using a class instead of a constant string means that resizing terminal during
    runtime won't run into issues.
    """

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return "=" * os.get_terminal_size().columns

    def ins(self, x: Str_able) -> str:
        w = os.get_terminal_size().columns
        rx = repr(x)
        if len(rx) > w:
            return rx
        return (
            "=" * ((w - len(rx)) // 2)
            + repr(x)
            + "=" * (((w - len(rx)) // 2) + ((w - len(rx))) % 2)
        )


sep = Separator()


todo_emoji = "📋"
warning_emoji = "<:pepebruh:1143287050079064115>"
