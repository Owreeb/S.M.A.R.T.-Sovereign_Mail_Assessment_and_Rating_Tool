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


def migrate_legacy_schema(engine: Engine) -> None:
    """
    Apply one-off schema migrations that create_all can not do on its own.

    create_all only creates missing tables, it never adds a column to an
    existing one. mail_system_ip_history gained an organisation_id column (IP
    links are now scoped per organisation). If a database still has the old
    table without that column, drop it here so create_all rebuilds it. Its rows
    were the globally-pooled links and get repopulated on the next scan anyway.

    Args:
        engine: The engine whose database to migrate.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "mail_system_ip_history" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("mail_system_ip_history")}
    if "organisation_id" not in columns:
        print("Migrating: dropping legacy mail_system_ip_history (rebuilt org-scoped)")
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE mail_system_ip_history"))
