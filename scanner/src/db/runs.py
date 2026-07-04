"""logs every scanner run in the scanner_runs table"""

from __future__ import annotations

import subprocess
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator

from sqlalchemy.orm import Session

from .models import ScannerRun


def get_git_hash() -> str | None:
    """current git commit hash, or None if git isn't there"""
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
    """make a ScannerRun row, yield it, stamp finished_at on exit"""
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
