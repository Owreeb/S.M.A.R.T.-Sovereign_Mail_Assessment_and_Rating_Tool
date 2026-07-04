"""history/upsert helpers for the db tables"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ScannerRun


def get_or_create(session: Session, model: type, **match: Any) -> tuple[Any, bool]:
    """find a row matching **match, or make one. returns (row, created)"""
    stmt = select(model)
    for key, value in match.items():
        stmt = stmt.where(getattr(model, key) == value)
    row = session.scalars(stmt).first()
    if row is not None:
        return row, False

    row = model(**match)
    session.add(row)
    return row, True


def get_current(session: Session, model: type, **match: Any) -> Any:
    """current row (is_current=True) for **match, or None"""
    stmt = select(model).where(model.is_current.is_(True))
    for key, value in match.items():
        stmt = stmt.where(getattr(model, key) == value)
    return session.scalars(stmt).first()


def update_fields(row: Any, values: dict[str, Any]) -> bool:
    """set the given fields on row, True if anything actually changed"""
    changed = False
    for key, value in values.items():
        if getattr(row, key) != value:
            setattr(row, key, value)
            changed = True
    return changed


def update_history(
    session: Session,
    model: type,
    run: ScannerRun,
    match: dict[str, Any],
    tracked: dict[str, Any],
) -> Any:
    """
    upsert a versioned history row for `match`, tracking `tracked`.

    nothing changed -> return current row. changed in the same run -> update in
    place. changed across runs -> close the old row, open a new one.
    """
    current = get_current(session, model, **match)

    if current is not None:
        same = all(getattr(current, key) == value for key, value in tracked.items())
        if same:
            return current
        if current.valid_from_run == run.id:
            for key, value in tracked.items():
                setattr(current, key, value)
            return current
        current.is_current = False
        current.valid_to_run = run.id

    new_row = model(
        valid_from_run=run.id,
        is_current=True,
        **match,
        **tracked,
    )
    session.add(new_row)
    return new_row
