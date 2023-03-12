import os
import pickle
import queue
import threading
import time
from typing import List
import discord

from core.task import Task


class PersistentInfo:
    def __init__(self, client: discord.Client) -> None:
        self._tasks: List[Task] = []
        self.alert_channels: List[discord.abc.MessageableChannel] = []

        if os.path.exists("data"):
            with open("data", "rb") as f:
                self.__dict__ = pickle.load(f)
                self.alert_channels = [
                    *map(
                        client.get_partial_messageable,
                        self.__dict__["alert_channel_ids"],
                    )
                ]

        self.message_queue = queue.Queue[bool]()

        writer_thread = threading.Thread(target=self.save_thread)
        writer_thread.daemon = True
        writer_thread.start()

    @property
    def tasks(self) -> List[Task]:
        return self._tasks

    @tasks.setter
    def tasks(self, new_tasks: List[Task]) -> None:
        self.message_queue.put(True)
        self._tasks = new_tasks

    def save_thread(self) -> None:
        while True:
            _ = self.message_queue.get()
            time.sleep(2)
            self.save()
            self.message_queue.task_done()

    def save(self) -> None:
        self_dict = dict(self.__dict__)
        self_dict["alert_channel_ids"] = [
            channel.id for channel in self.alert_channels
        ]
        del self_dict["alert_channels"]
        del self_dict["message_queue"]
        with open("data", "wb") as f:
            pickle.dump(self_dict, f)
