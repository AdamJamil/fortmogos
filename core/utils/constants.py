import os
import discord


with open("token.txt", "r") as f:
    TOKEN, TEST_TOKEN = f.read().strip().split("\n")

fortmogos_id = 1061719682773688391

GUILD = "suspcious"

client = discord.Client(intents=discord.Intents.all())

test_channel_id = 1063934130397659236
test_client = discord.Client(intents=discord.Intents.all())


def get_test_channel() -> discord.PartialMessageable:
    return test_client.get_partial_messageable(test_channel_id)


sep = "=" * os.get_terminal_size().columns
