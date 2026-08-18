"""Загрузка, переопределение и строгая проверка конфигурации."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


VALID_CASES = {"nominative", "genitive", "dative", "accusative", "instrumental", "prepositional"}


class ConfigError(ValueError):
    """Понятная пользователю ошибка конфигурации."""


@dataclass(frozen=True)
class GenerationConfig:
    count: int
    seed: int | None
    unique_records: bool


@dataclass(frozen=True)
class AppConfig:
    source_path: Path
    generation: GenerationConfig
    fields: dict[str, bool]
    male_percent: int
    female_percent: int
    origins: dict[str, int]
    min_date: date
    max_date: date
    date_format: str
    phone_prefix: str
    phone_digits: int
    phone_format: str
    declension_enabled: bool
    declension_case: str
    exclusions_enabled: bool
    exclusions_directory: Path
    output_path: Path
    delimiter: str
    encoding: str
    data_directory: Path


def _require_dict(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"Раздел '{name}' должен быть JSON-объектом.")
    return value


def _percentages(section: dict[str, Any], names: tuple[str, ...], label: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for name in names:
        value = section.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
            raise ConfigError(f"'{label}.{name}' должен быть целым числом от 0 до 100.")
        values[name] = value
    if sum(values.values()) != 100:
        raise ConfigError(f"Сумма процентов в '{label}' должна быть равна 100.")
    return values


def _as_path(value: Any, label: str, base: Path) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"'{label}' должен быть непустой строкой пути.")
    path = Path(value)
    return path if path.is_absolute() else base / path


def load_config(path: str | Path, overrides: dict[str, Any] | None = None) -> AppConfig:
    """Загрузить JSON-файл, применить CLI-переопределения и проверить схему."""
    source = Path(path).resolve()
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigError(f"Файл конфигурации не найден: {source}") from error
    except json.JSONDecodeError as error:
        raise ConfigError(f"Некорректный JSON в {source}: {error.msg} (строка {error.lineno}).") from error
    root = _require_dict(raw, "root")
    generation = _require_dict(root.get("generation"), "generation")
    if overrides:
        for key in ("count", "seed"):
            if overrides.get(key) is not None:
                generation[key] = overrides[key]
        if overrides.get("output") is not None:
            _require_dict(root.get("output"), "output")["path"] = overrides["output"]
    count = generation.get("count")
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise ConfigError("'generation.count' должен быть положительным целым числом.")
    seed = generation.get("seed")
    if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool)):
        raise ConfigError("'generation.seed' должен быть целым числом или null.")
    unique = generation.get("unique_records", False)
    if not isinstance(unique, bool):
        raise ConfigError("'generation.unique_records' должен быть true или false.")
    fields = _require_dict(root.get("fields"), "fields")
    allowed_fields = ("surname", "name", "patronymic", "gender", "birth_date", "phone", "birth_city", "origin")
    unknown = set(fields) - set(allowed_fields)
    if unknown:
        raise ConfigError(f"Неизвестные поля в 'fields': {', '.join(sorted(unknown))}.")
    normalized_fields: dict[str, bool] = {}
    for field in allowed_fields:
        value = fields.get(field, False)
        if not isinstance(value, bool):
            raise ConfigError(f"'fields.{field}' должен быть true или false.")
        normalized_fields[field] = value
    gender = _percentages(_require_dict(root.get("gender"), "gender"), ("male_percent", "female_percent"), "gender")
    origin_section = _require_dict(root.get("origin"), "origin")
    origin_percents = _percentages(origin_section, ("russia_percent", "cis_percent"), "origin")
    origins = {"Russia": origin_percents["russia_percent"], "CIS": origin_percents["cis_percent"]}
    birth = _require_dict(root.get("birth_date"), "birth_date")
    try:
        min_date, max_date = date.fromisoformat(birth["min_date"]), date.fromisoformat(birth["max_date"])
    except (KeyError, TypeError, ValueError) as error:
        raise ConfigError("'birth_date.min_date' и 'birth_date.max_date' должны иметь вид YYYY-MM-DD.") from error
    if min_date > max_date:
        raise ConfigError("'birth_date.min_date' не может быть позже 'max_date'.")
    date_format = birth.get("format", "%d.%m.%Y")
    if not isinstance(date_format, str) or not date_format:
        raise ConfigError("'birth_date.format' должен быть непустой строкой.")
    phone = _require_dict(root.get("phone"), "phone")
    digits = phone.get("digits_after_prefix")
    if not isinstance(digits, int) or isinstance(digits, bool) or digits <= 0:
        raise ConfigError("'phone.digits_after_prefix' должен быть положительным целым числом.")
    prefix, pattern = phone.get("prefix"), phone.get("format")
    if not isinstance(prefix, str) or not isinstance(pattern, str) or not pattern:
        raise ConfigError("'phone.prefix' и 'phone.format' должны быть непустыми строками.")
    if pattern.count("#") != digits:
        raise ConfigError("Количество '#' в 'phone.format' должно совпадать с 'digits_after_prefix'.")
    declension = _require_dict(root.get("declension"), "declension")
    case = declension.get("case", "genitive")
    if case not in VALID_CASES:
        raise ConfigError("Неизвестный падеж. Допустимы: " + ", ".join(sorted(VALID_CASES)) + ".")
    exclusions = _require_dict(root.get("exclusions"), "exclusions")
    output = _require_dict(root.get("output"), "output")
    base = source.parent
    delimiter, encoding = output.get("delimiter", ";"), output.get("encoding", "utf-8-sig")
    if not isinstance(delimiter, str) or len(delimiter) != 1:
        raise ConfigError("'output.delimiter' должен состоять из одного символа.")
    if not isinstance(encoding, str) or not encoding:
        raise ConfigError("'output.encoding' должен быть непустой строкой.")
    data_dir = _as_path(root.get("data_directory", "data"), "data_directory", base)
    declension_enabled = declension.get("enabled", False)
    exclusions_enabled = exclusions.get("enabled", False)
    if not isinstance(declension_enabled, bool) or not isinstance(exclusions_enabled, bool):
        raise ConfigError("Параметры 'declension.enabled' и 'exclusions.enabled' должны быть true или false.")
    return AppConfig(source, GenerationConfig(count, seed, unique), normalized_fields, gender["male_percent"], gender["female_percent"], origins, min_date, max_date, date_format, prefix, digits, pattern, declension_enabled, case, exclusions_enabled, _as_path(exclusions.get("directory", "exclusions"), "exclusions.directory", base), _as_path(output.get("path"), "output.path", base), delimiter, encoding, data_dir)
