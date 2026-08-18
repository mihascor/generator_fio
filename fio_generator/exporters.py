"""Подготовка и экспорт CSV."""

import csv
from pathlib import Path

from .config import AppConfig
from .declension import NameDeclensor
from .models import Person


def person_row(person: Person, config: AppConfig, declensor: NameDeclensor | None = None) -> dict[str, str | int]:
    values: dict[str, str | int] = {"id": person.id}
    raw = {"surname": person.surname, "name": person.name, "patronymic": person.patronymic, "gender": person.gender.value, "birth_date": person.birth_date.strftime(config.date_format), "phone": person.phone, "birth_city": person.birth_city, "origin": person.origin}
    for field in ("surname", "name", "patronymic", "gender", "birth_date", "phone", "birth_city", "origin"):
        enabled = config.fields[field]
        if enabled:
            values[field] = raw[field]
    names = [raw[field] for field in ("surname", "name", "patronymic") if config.fields[field]]
    if config.fields["full_name"]:
        values["full_name"] = " ".join(names)
    if config.declension_enabled and declensor:
        declined = {"surname": declensor.decline_surname(person.surname, person.gender, config.declension_case), "name": person.name, "patronymic": declensor.decline_patronymic(person.patronymic, person.gender, config.declension_case)}
        for field in ("surname", "name", "patronymic"):
            if config.fields[field]:
                values[f"{field}_declined"] = declined[field]
        if config.fields["full_name"]:
            values["full_name_declined"] = " ".join(declined[field] for field in ("surname", "name", "patronymic") if config.fields[field])
    return values


def export_csv(people: list[Person], config: AppConfig) -> Path:
    """Сохранить результат, создав родительский каталог при необходимости."""
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    declensor = NameDeclensor() if config.declension_enabled else None
    rows = [person_row(person, config, declensor) for person in people]
    fields = list(rows[0]) if rows else ["id"]
    with config.output_path.open("w", encoding=config.encoding, newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, delimiter=config.delimiter)
        writer.writeheader()
        writer.writerows(rows)
    return config.output_path
