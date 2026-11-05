"""In-memory OCR session store for M13 (D-12).

Thread-safe dictionary protected by threading.Lock.
Orphan file cleanup on startup (D-13).
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Dict, Optional

from app.ocr.schemas import OCRSession

logger = logging.getLogger(__name__)


class OCRSessionStore:
    """Thread-safe in-memory store for OCR sessions."""

    def __init__(self) -> None:
        self._sessions: Dict[str, OCRSession] = {}
        self.lock = threading.Lock()

    def add(self, session: OCRSession) -> None:
        """Add a session to the store."""
        with self.lock:
            self._sessions[session.session_id] = session

    def get(self, session_id: str) -> Optional[OCRSession]:
        """Get a session by ID."""
        with self.lock:
            return self._sessions.get(session_id)

    def update(self, session: OCRSession) -> None:
        """Update an existing session."""
        with self.lock:
            if session.session_id in self._sessions:
                self._sessions[session.session_id] = session

    def remove(self, session_id: str) -> None:
        """Remove a session from the store."""
        with self.lock:
            self._sessions.pop(session_id, None)

    def __contains__(self, session_id: str) -> bool:
        with self.lock:
            return session_id in self._sessions

    def try_claim_confirming(self, session_id: str) -> Optional[OCRSession]:
        """Atomically transition a session from 'completed' to 'confirming'.

        Returns the session if the transition succeeds, or None if the session
        does not exist or is not in 'completed' status.

        This is the gate that prevents two concurrent confirmation requests
        from proceeding simultaneously on the same session.
        """
        with self.lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if session.status != "completed":
                return None
            session.status = "confirming"  # type: ignore[assignment]
            return session

    def try_claim_reprocess(self, session_id: str) -> Optional[OCRSession]:
        """Atomically transition a session from 'failed' to 'pending'.

        Returns the session if the transition succeeds, or None if the session
        does not exist or is not in 'failed' status.

        This is the gate that prevents two concurrent reprocess requests
        from proceeding simultaneously on the same session.
        """
        with self.lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if session.status != "failed":
                return None
            session.status = "pending"  # type: ignore[assignment]
            return session

    def restore_completed(self, session_id: str) -> None:
        """Restore a session from 'confirming' back to 'completed'.

        Used on pre-commit failures so the operator can retry confirmation.
        """
        with self.lock:
            session = self._sessions.get(session_id)
            if session is not None and session.status == "confirming":
                session.status = "completed"  # type: ignore[assignment]


# Global store instance — shared across the single-process backend.
store = OCRSessionStore()


def cleanup_orphan_files(upload_dir: Path, max_age_seconds: int = 3600) -> int:
    """Remove orphaned files in the OCR upload directory.

    Called on startup to clean up files left by previous process crashes.
    Returns the number of files removed.
    """
    if not upload_dir.exists():
        return 0

    now = time.time()
    removed = 0
    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            age = now - file_path.stat().st_mtime
            if age > max_age_seconds:
                try:
                    file_path.unlink()
                    logger.info("Removed orphan OCR file: %s (age: %.0fs)", file_path.name, age)
                    removed += 1
                except OSError as exc:
                    logger.warning("Failed to remove orphan file %s: %s", file_path.name, exc)
    return removed
