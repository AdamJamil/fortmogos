from typing import cast
from sqlalchemy.ext.declarative import declarative_base  # type: ignore

Base: type = cast(type, declarative_base())
