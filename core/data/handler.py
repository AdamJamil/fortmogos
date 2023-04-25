from functools import cache
import threading
from typing import (
    Any,
    Awaitable,
    Callable,
    Iterable,
    List,
    Optional,
    Set,
    SupportsIndex,
    Tuple,
    TypeVar,
)
import discord
from core.data.db import session
from core.data.writable import AlertChannel, Task
from core.utils.walk import subclasses_of

T = TypeVar("T")


class DBLock:
    def __init__(self) -> None:
        self.lock = threading.Lock()

    def acquire(self):
        self.lock.acquire()

    def release(self):
        self.lock.release()
        session.commit()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *_: Tuple[Any, ...]) -> None:
        self.release()


class AtomicDBList(list[T]):
    @staticmethod
    @cache
    def unsupported_methods() -> Set[str]:
        return set(name for name in dir(list) if not hasattr(AtomicDBList, name))

    def __getattribute__(self, name: str) -> Any:
        if name in AtomicDBList.unsupported_methods():
            raise NotImplementedError(f"Method '{name}' not supported in AtomicDBList")
        return super().__getattribute__(name)

    def __init__(self, items: Optional[List[T]] = None) -> None:
        super().__init__()
        self.lock = threading.Lock()
        super().extend(items or [])

    def append(self, item: T) -> None:
        with self.lock:
            super().append(item)
            session.add(item)
            session.commit()

    def extend(self, iterable: Iterable[T]) -> None:
        with self.lock:
            for item in iterable:
                self.session.add(item)
                super().append(item)
            session.commit()

    def insert(self, index: SupportsIndex, item: T) -> None:
        with self.lock:
            super().insert(index, item)
            session.add(item)
            session.commit()

    def remove(self, item: T) -> None:
        with self.lock:
            super().remove(item)
            session.delete(item)
            session.commit()

    def pop(self, index: SupportsIndex = -1) -> T:
        with self.lock:
            item = super().pop(index)
            session.delete(item)
            session.commit()
            return item

    def clear(self) -> None:
        with self.lock:
            for item in self:
                session.delete(item)
            super().clear()
            session.commit()

    async def async_filter(self, filter: Callable[[T], Awaitable[bool]]) -> None:
        with self.lock:
            empty_idx = 0
            for i in range(len(self)):
                if await filter(self[i]):
                    super().__setitem__(empty_idx, super().__getitem__(i))
                    empty_idx += 1
            for i in range(len(self) - empty_idx):
                super().pop()
            session.commit()

    def __setitem__(self, index: int, item: T) -> None:
        with self.lock:
            self.session.delete(self[index])
            self[index] = item
            session.add(item)
            session.commit()


class DataHandler:
    def __init__(self, client: discord.Client) -> None:
        self.tasks: AtomicDBList[Task] = AtomicDBList(
            [
                x
                for subcls in subclasses_of(Task)
                if hasattr(subcls, "__tablename__")
                for x in (session.query(subcls)).all()
            ]
        )
        self.alert_channels: AtomicDBList[AlertChannel] = AtomicDBList(
            session.query(AlertChannel).all()
        )
        self.client = client

    def __setattr__(self, __name: str, __value: Any) -> None:
        if hasattr(self, __name) and isinstance(getattr(self, __name), AtomicDBList):
            raise TypeError("Cannot reassign AtomicDBList")

        super().__setattr__(__name, __value)
