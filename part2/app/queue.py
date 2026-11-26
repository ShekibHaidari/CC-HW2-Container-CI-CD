
"""File-based FIFO queue with safe concurrent access."""

from __future__ import annotations

import fcntl
import os
import tempfile
from pathlib import Path


def join(path: str | Path, name: str) -> int:
    """Add a person and return the current queue length."""

    # Validate before touching the queue or lock file.
    if not isinstance(name, str):
        raise TypeError("Name must be a string")

    if "\n" in name or "\r" in name:
        raise ValueError("Newlines are not allowed")

    name = name.strip()

    if not name or len(name) > 40:
        raise ValueError("Invalid name")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lock_path = path.parent / "queue.lock"

    with open(lock_path, "a+b") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)

        try:
            if path.exists():
                names = path.read_text(
                    encoding="utf-8"
                ).splitlines()
            else:
                names = []

            names.append(name)

            path.write_text(
                "\n".join(names) + "\n",
                encoding="utf-8"
            )

            return len(names)

        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


def take(path: str | Path) -> str:
    """Remove and return the first person safely."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lock_path = path.parent / "queue.lock"

    with open(lock_path, "a+b") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)

        try:
            if not path.exists():
                raise LookupError("Queue is empty")

            names = path.read_text(
                encoding="utf-8"
            ).splitlines()

            if not names:
                raise LookupError("Queue is empty")

            first = names.pop(0)
            remaining = (
                "\n".join(names) + "\n" if names else ""
            )

            # Write to a unique temporary file.
            temp_path = None

            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=path.parent,
                    prefix=".queue-",
                    delete=False
                ) as temp_file:
                    temp_path = Path(temp_file.name)
                    temp_file.write(remaining)

                # Atomically replace the original queue file.
                os.replace(temp_path, path)

            finally:
                if temp_path is not None:
                    temp_path.unlink(missing_ok=True)

            return first

        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
