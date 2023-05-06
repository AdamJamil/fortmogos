from functools import cache
import threading
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    SupportsIndex,
    Tuple,
    TypeVar,
    cast,
)
import discord
from core.data.base import Base
from core.data.db import session
from core.data.writable import AlertChannel, Task, Timezone
from core.utils.exceptions import MissingTimezoneException
from core.utils.walk import subclasses_of

T = TypeVar("T", bound=Base)
K, V = TypeVar("K"), TypeVar("V", bound=Base)


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
                session.delete(super().__getitem__(-1))
                super().pop()
            session.commit()

    def __setitem__(self, index: int, item: T) -> None:
        with self.lock:
            self.session.delete(self[index])
            self[index] = item
            session.add(item)
            session.commit()


class AtomicDBDict(dict[K, V]):
    @staticmethod
    @cache
    def unsupported_methods() -> Set[str]:
        return set(name for name in dir(dir) if not hasattr(AtomicDBDict, name))

    def __getattribute__(self, name: str) -> Any:
        if name in AtomicDBDict.unsupported_methods():
            raise NotImplementedError(f"Method '{name}' not supported in AtomicDBDict")
        return super().__getattribute__(name)

    def __init__(self, items: Optional[Dict[K, V]] = None) -> None:
        super().__init__()
        self.lock = threading.Lock()
        super().update(items or {})

    def __getitem__(self, key: K) -> V:
        with self.lock:
            if not super().__contains__(key):
                raise MissingTimezoneException(
                    "Please report your timezone first! Report one of the following: "
                    "the current time in your area `timezone 4:20PM`; the offset "
                    "`timezone UTC+5`; the region name `timezone US/Eastern`."
                )
            return super().__getitem__(key)

    def __setitem__(self, key: K, value: V) -> None:
        with self.lock:
            if super().__contains__(key):
                session.delete(super().__getitem__(key))
            session.add(value)
            super().__setitem__(key, value)
            session.commit()

    def clear(self) -> None:
        with self.lock:
            for _, value in super().items():
                session.delete(value)
            super().clear()
            session.commit()


class DataHandler:
    def __init__(self, client: discord.Client) -> None:
        self.client = client

    def populate_data(self) -> None:
        """
        Delayed from init. This is because we need the client to be initialized
        before calling the reconstructor for AlertChannel.
        """
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
        self.timezones: AtomicDBDict[int, Timezone] = AtomicDBDict(
            {cast(int, tz._id): tz for tz in session.query(Timezone).all()}
        )

    def __setattr__(self, __name: str, __value: Any) -> None:
        if hasattr(self, __name) and isinstance(getattr(self, __name), AtomicDBList):
            raise TypeError("Cannot reassign AtomicDBList")

        super().__setattr__(__name, __value)
