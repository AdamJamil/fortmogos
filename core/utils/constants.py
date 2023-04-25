import os
import discord

from custom_typing.protocols import Str_able


with open("token.txt", "r") as f:
    TOKEN, TEST_TOKEN, FAKE_TOKEN = f.read().strip().split("\n")


def get_token():
    return TOKEN


def get_test_token():
    return TEST_TOKEN


fakemogus_id = 1089042918259564564
testmogus_id = 1074389982095089664

GUILD = "suspcious"

client = discord.Client(intents=discord.Intents.all())

test_channel_id = 1089045607840231505
test_client = discord.Client(intents=discord.Intents.all())


# TODO: figure out how to mock this more accurately
def get_test_channel() -> discord.PartialMessageable:
    return test_client.get_partial_messageable(test_channel_id)


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
