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
    overload,
)
import discord
from core.data.db import session
from core.data.writable import Alert, AlertChannel, Task, Timezone, UserTask, Wakeup
from core.utils.exceptions import MissingTimezoneException
from core.utils.walk import subclasses_of
from custom_typing.protocols import Writable

T = TypeVar("T", bound=Writable | Task)


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

    @overload
    def __setitem__(self, index: SupportsIndex, item: T) -> None:
        ...

    @overload
    def __setitem__(self, index: slice, item: Iterable[T]) -> None:
        ...

    def __setitem__(self, index, item) -> None:
        with self.lock:
            if isinstance(index, slice):
                raise TypeError("why")
            else:
                self.session.delete(self[index])
                self[index] = item
                session.add(item)
                session.commit()


K = TypeVar("K")
V = TypeVar("V", bound=Writable)


class AtomicDBDict(dict[K, V]):
    @staticmethod
    @cache
    def unsupported_methods() -> Set[str]:
        return set(name for name in dir(dir) if not hasattr(AtomicDBDict, name))

    def __getattribute__(self, name: str) -> Any:
        if name in AtomicDBDict.unsupported_methods():
            raise NotImplementedError(f"Method '{name}' not supported in AtomicDBDict")
        return super().__getattribute__(name)

    def __init__(self, items: Optional[Dict[K, V]] = None, tz: bool = False) -> None:
        super().__init__()
        self.lock = threading.Lock()
        self.tz = tz
        super().update(items or {})

    def __getitem__(self, key: K) -> V:
        with self.lock:
            if self.tz and not super().__contains__(key):
                raise MissingTimezoneException()
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

    def keys(self):
        return super().keys()

    async def async_lambda(self, call: Callable[[K, V], Awaitable[None]]) -> None:
        with self.lock:
            for k, v in self.items():
                await call(k, v)


class DataHandler:
    _instance: Optional["DataHandler"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        self.reminder_msgs: Dict[Tuple[int, discord.Message], Alert] = {}

    def populate_data(self) -> None:
        """
        Delayed from init. This is because we need the client to be initialized
        before calling the reconstructor for AlertChannel.
        """
        self.tasks: AtomicDBList[Task] = AtomicDBList(
            [
                x
                for subcls in subclasses_of(Task)
                if hasattr(subcls, "__tablename__") and subcls != Wakeup
                for x in (session.query(subcls)).all()
            ]
        )
        self.alert_channels: AtomicDBList[AlertChannel] = AtomicDBList(
            session.query(AlertChannel).all()
        )
        self.timezones: AtomicDBDict[int, Timezone] = AtomicDBDict(
            {cast(int, tz._id): tz for tz in session.query(Timezone).all()}, tz=True
        )
        self.user_tasks: AtomicDBList[UserTask] = AtomicDBList(
            session.query(UserTask).all()
        )
        self.wakeup: AtomicDBDict[int, Wakeup] = AtomicDBDict(
            {cast(int, wakeup.user): wakeup for wakeup in session.query(Wakeup).all()}
        )

    def __setattr__(self, __name: str, __value: Any) -> None:
        if hasattr(self, __name) and isinstance(getattr(self, __name), AtomicDBList):
            raise TypeError("Cannot reassign AtomicDBList")

        super().__setattr__(__name, __value)
