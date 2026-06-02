"""Helper to log every scanner run in the scanner_runs table."""

from __future__ import annotations

import subprocess
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from sqlalchemy.orm import Session

from .models import ScannerRun


def get_git_hash() -> str | None:
    """
    Gets the current git commit hash.

    Returns:
        The hash, or None if git is not there or it fails.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


@contextmanager
def scanner_run(session: Session) -> Iterator[ScannerRun]:
    """
    Makes a ScannerRun row and sets the end time when the block is done.

    Args:
        session: The session to save the run with.
        git_hash: The scanner version. If None it tries to read it from git.

    Yields:
        The new ScannerRun.
    """
    git_hash = get_git_hash()

    run = ScannerRun(
        started_at=datetime.now(timezone.utc),
        scanner_version_git_hash=git_hash,
    )
    session.add(run)
    session.commit()

    try:
        yield run
    finally:
        run.finished_at = datetime.now(timezone.utc)
        session.commit()
