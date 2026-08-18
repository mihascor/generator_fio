"""Сортировка и очистка текстового справочника."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path


def normalize_dictionary(path: Path) -> tuple[int, int]:
    """Удалить пустые строки/дубли, отсортировать значения и заменить файл.

    Дубли сравниваются без учёта регистра и пробелов по краям. Возвращаются
    количество исходных непустых строк и число записанных уникальных значений.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Файл не найден: {path}")
    raw_values = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    unique: dict[str, str] = {}
    for value in raw_values:
        unique.setdefault(value.casefold(), value)
    values = sorted(unique.values(), key=lambda value: value.casefold())

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as temporary:
        temporary.write("\n".join(values))
        if values:
            temporary.write("\n")
        temporary_path = Path(temporary.name)
    try:
        os.replace(temporary_path, path)
    except OSError:
        temporary_path.unlink(missing_ok=True)
        raise
    return len(raw_values), len(values)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Отсортировать справочник и удалить дубли прямо в исходном файле.")
    parser.add_argument("path", type=Path, help="Путь к .txt-файлу справочника.")
    args = parser.parse_args(argv)
    try:
        before, after = normalize_dictionary(args.path)
    except (OSError, UnicodeError) as error:
        parser.error(str(error))
    print(f"Готово: {args.path} — было строк: {before}, уникальных записей: {after}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
