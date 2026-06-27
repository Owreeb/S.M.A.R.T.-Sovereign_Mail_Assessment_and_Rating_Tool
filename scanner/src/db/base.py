"""
Setup for the database.

This file has the SQLAlchemy Base and some helper functions.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Base class that all the models use."""


def make_engine(db_path: str | Path, *, echo: bool = False) -> Engine:
    """
    Makes a SQLite engine for the database file.

    Args:
        db_path: Path to the SQLite file. The folder is created if it is
            not there yet.
        echo: If True, prints the SQL that gets run.

    Returns:
        A SQLAlchemy engine.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{path}", echo=echo)


def make_session(engine: Engine) -> sessionmaker:
    """
    Makes a sessionmaker for the given engine.

    Args:
        engine: The engine the sessions should use.

    Returns:
        A sessionmaker.
    """
    return sessionmaker(bind=engine, expire_on_commit=False)


def create_all(engine: Engine) -> None:
    """Creates all the tables if they don't exist yet.

    Args:
        engine: The engine to create the tables on.
    """
    Base.metadata.create_all(engine)
