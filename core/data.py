import os
import pickle
from typing import List

import discord


class PersistentInfo:
    def __init__(self, client: discord.Client) -> None:
        from core.alert import Alert

        self.alerts: List[Alert] = []
        self.alert_channels: List[discord.abc.MessageableChannel] = []

        if os.path.exists("data"):
            with open("data", "rb") as f:
                self.__dict__ = pickle.load(f).__dict__
                self.alert_channels = [
                    *map(client.get_partial_messageable, self.alert_channels_ids)
                ]

    def save(self) -> List["discord.abc.MessageableChannel"]:
        self.alert_channels_ids = [channel.id for channel in self.alert_channels]
        shit = self.alert_channels
        delattr(self, "alert_channels")
        with open("data", "wb") as f:
            pickle.dump(self, f)
        self.alert_channels = shit
        return shit
