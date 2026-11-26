
"""Simple file-based FIFO queue."""

from __future__ import annotations

from pathlib import Path


def join(path: str | Path, name: str) -> int:
    """Add a name to the queue and return its ticket number."""

    if not isinstance(name, str):
        raise ValueError("Name must be a string")

    # Validate before changing the queue file.
    if "\n" in name or "\r" in name:
        raise ValueError("Newlines are not allowed")

    name = name.strip()

    if not name or len(name) > 40:
        raise ValueError("Invalid name")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        names = path.read_text(encoding="utf-8").splitlines()
    else:
        names = []

    names.append(name)

    path.write_text(
        "\n".join(names) + "\n",
        encoding="utf-8"
    )

    return len(names)


def take(path: str | Path) -> str:
    """Remove and return the first person in the queue."""

    path = Path(path)

    if not path.exists():
        raise LookupError("Queue is empty")

    names = path.read_text(encoding="utf-8").splitlines()

    if not names:
        raise LookupError("Queue is empty")

    first = names.pop(0)

    path.write_text(
        "\n".join(names) + ("\n" if names else ""),
        encoding="utf-8"
    )

    return first
