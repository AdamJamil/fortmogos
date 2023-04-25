"""
Imports all classes which we expect to write to db, and sets up db connection.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.data.base import Base
from core.utils.walk import subclasses_of

# this call imports any subclass of Base internally, which is what we want
subclasses_of(Base)

engine = create_engine("sqlite:///data.db")
Base.metadata.create_all(engine, checkfirst=True)
Session = sessionmaker(bind=engine)
session = Session()
