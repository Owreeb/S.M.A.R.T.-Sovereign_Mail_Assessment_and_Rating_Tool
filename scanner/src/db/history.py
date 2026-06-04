"""
Helper functions for the DB Tables.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import ScannerRun


def get_or_create(session: Session, model: type, **match: Any) -> tuple[Any, bool]:
    """
    Looks for a row that matches, and makes a new one if there isn't any.

    Args:
        session: The session.
        model: The model class, e.g. Organisation.
        **match: The columns we use to find the row.

    Returns:
        A tuple (row, created). created is True if we had to make it new.
    """
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
    """
    Gets the current row (is_current = True) for the match, or None.

    Args:
        session: The session.
        model: The history model class, e.g. OrgDomainHistory.
        **match: The columns that say which history  it is.

    Returns:
        The current row, or None if there isn't one yet.
    """
    stmt = select(model).where(model.is_current.is_(True))
    for key, value in match.items():
        stmt = stmt.where(getattr(model, key) == value)
    return session.scalars(stmt).first()


def update_fields(row: Any, values: dict[str, Any]) -> bool:
    """
    Updarte the fields on a row, but only the ones that are not the same.

    Args:
        row: The object we want to change.
        values: A dict of field name -> new value.

    Returns:
        True if we changed at least one field.
    """
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
    Keep history up to date.

    It searches the current row for the thing in `match`.
    If the tracked values are still the same we do nothing. If the current
    row created in ths same run, we just update it in place. 
    If it is from an older run we close itand add a new current row
    that starts with this run.

    Args:
        session: The session.
        model: The history model class, e.g. OrgDomainHistory.
        run: The current ScannerRun. We use its id for valid_from_run.
        match: The columns that say which history chain it is
        tracked: The columns that should make a new version if they change.

    Returns:
        The current history row 
    """
    current = get_current(session, model, **match)

    if current is not None:
        # check if any tracked value is different than before
        same = all(getattr(current, key) == value for key, value in tracked.items())
        if same:
            return current
        if current.valid_from_run == run.id:
            # this row was already made in this run, so just change it
            for key, value in tracked.items():
                setattr(current, key, value)
            return current
        # the row is from an older run, so we close it
        current.is_current = False
        current.valid_to_run = run.id

    # add the new version that is valid from now on
    new_row = model(
        valid_from_run=run.id,
        is_current=True,
        **match,
        **tracked,
    )
    session.add(new_row)
    return new_row
