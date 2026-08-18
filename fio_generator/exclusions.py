"""Чтение списков исключений."""

from pathlib import Path

def load_exclusions(directory: Path, enabled: bool) -> dict[str, set[str]]:
    if not enabled:
        return {}
    result: dict[str, set[str]] = {}
    for category in ("names", "surnames", "patronymics", "cities"):
        path = directory / f"{category}.txt"
        if not path.exists():
            result[category] = set()
            continue
        result[category] = {line.strip().casefold() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}
    return result
