import os
import discord

from custom_typing.protocols import Repr_able


with open("token.txt", "r") as f:
    TOKEN, TEST_TOKEN = f.read().strip().split("\n")

fortmogos_id = 1061719682773688391

GUILD = "suspcious"

client = discord.Client(intents=discord.Intents.all())

test_channel_id = 1063934130397659236
test_client = discord.Client(intents=discord.Intents.all())


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

    def ins(self, x: Repr_able) -> str:
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
