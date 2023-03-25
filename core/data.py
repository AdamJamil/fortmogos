import os
import pickle
import queue
import threading
import time
from typing import Any, Awaitable, Callable, List
import discord

from core.task import Task


class FakeList(list[Task]):
    def __getattribute__(self, name: str) -> Any:
        if name not in ["__len__", "__idx__"]:
            raise NotImplementedError(f"{name} is not okay!!!!!!")
        return super().__getattribute__(name)


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
        self.lock = threading.Lock()

        writer_thread = threading.Thread(target=self.save_thread)
        writer_thread.daemon = True
        writer_thread.start()

    @property
    def tasks(self) -> FakeList:
        return FakeList(self._tasks)

    @tasks.setter
    def tasks(self, _: Any) -> None:
        raise NotImplementedError()

    def append_task(self, task: Task) -> None:
        with self.lock:
            self._tasks.append(task)
        self.message_queue.put(True)

    def remove_task(self, task: Task) -> None:
        with self.lock:
            self._tasks.remove(task)
        self.message_queue.put(True)

    async def async_filter_tasks(
        self, filter: Callable[[Task], Awaitable[bool]]
    ) -> None:
        with self.lock:
            empty_idx = 0
            for i in range(len(self._tasks)):
                if await filter(self._tasks[i]):
                    self._tasks[empty_idx] = self._tasks[i]
                    empty_idx += 1
            for i in range(len(self._tasks) - empty_idx):
                self._tasks.pop()
        self.message_queue.put(True)

    def clear_tasks(self) -> None:
        with self.lock:
            self._tasks = []
        self.message_queue.put(True)

    def save_thread(self) -> None:
        while True:
            _ = self.message_queue.get()
            time.sleep(2)
            self.save()
            self.message_queue.task_done()

    def save(self) -> None:
        self_dict = dict(self.__dict__)
        self_dict["alert_channel_ids"] = [channel.id for channel in self.alert_channels]
        del self_dict["alert_channels"]
        del self_dict["message_queue"]
        del self_dict["lock"]
        with open("data", "wb") as f:
            pickle.dump(self_dict, f)
