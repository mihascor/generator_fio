"""Загрузка и подготовка внешних справочников имён."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import Gender


class DictionaryError(ValueError):
    """Справочник отсутствует или не содержит подходящих значений."""


@dataclass(frozen=True)
class OriginDictionary:
    male_names: tuple[str, ...]
    female_names: tuple[str, ...]
    male_surnames: tuple[str, ...]
    female_surnames: tuple[str, ...]
    male_patronymics: tuple[str, ...]
    female_patronymics: tuple[str, ...]
    cities: tuple[str, ...]

    def values(self, kind: str, gender: Gender) -> tuple[str, ...]:
        prefix = "male" if gender == Gender.MALE else "female"
        return getattr(self, f"{prefix}_{kind}s")


_FILES = ("male_names", "female_names", "male_surnames", "female_surnames", "male_patronymics", "female_patronymics", "cities")


def read_values(path: Path) -> tuple[str, ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as error:
        raise DictionaryError(f"Обязательный справочник не найден: {path}") from error
    result = tuple(dict.fromkeys(line.strip() for line in lines if line.strip()))
    if not result:
        raise DictionaryError(f"Справочник пуст: {path}")
    return result


def load_dictionaries(data_directory: Path, exclusions: dict[str, set[str]]) -> dict[str, OriginDictionary]:
    """Загрузить группы из data/russia и data/cis; легко расширяется новыми папками."""
    if not data_directory.is_dir():
        raise DictionaryError(f"Каталог справочников не найден: {data_directory}")
    dictionaries: dict[str, OriginDictionary] = {}
    for directory in data_directory.iterdir():
        if not directory.is_dir():
            continue
        values: dict[str, tuple[str, ...]] = {}
        for filename in _FILES:
            category = "cities" if filename == "cities" else filename.split("_", 1)[1]
            filtered = tuple(item for item in read_values(directory / f"{filename}.txt") if item.casefold().strip() not in exclusions.get(category, set()))
            if not filtered:
                raise DictionaryError(f"После исключений справочник пуст: {directory / (filename + '.txt')}")
            values[filename] = filtered
        label = "Russia" if directory.name.casefold() == "russia" else "CIS" if directory.name.casefold() == "cis" else directory.name
        dictionaries[label] = OriginDictionary(**values)
    for required in ("Russia", "CIS"):
        if required not in dictionaries:
            raise DictionaryError(f"Не найдена обязательная группа справочников: {required}.")
    return dictionaries
