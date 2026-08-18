"""Координация генерации записей."""

from __future__ import annotations

from collections import Counter
from random import Random

from .birthdate import random_birth_date
from .config import AppConfig
from .geography import choose_origin
from .models import Gender, Person
from .names import OriginDictionary
from .phone import generate_phone


class GenerationError(RuntimeError):
    """Запрошенная уникальная выборка не может быть построена."""


class PersonGenerator:
    """Генератор с собственным RNG для воспроизводимых результатов."""

    def __init__(self, config: AppConfig, dictionaries: dict[str, OriginDictionary]) -> None:
        self.config, self.dictionaries = config, dictionaries
        self.rng = Random(config.generation.seed)

    def generate(self) -> list[Person]:
        people: list[Person] = []
        seen: set[tuple[object, ...]] = set()
        attempts, maximum = 0, max(self.config.generation.count * 100, 1000)
        while len(people) < self.config.generation.count:
            person = self._one(len(people) + 1)
            key = (person.surname, person.name, person.patronymic, person.gender, person.birth_date, person.phone, person.birth_city, person.origin)
            if self.config.generation.unique_records and key in seen:
                attempts += 1
                if attempts >= maximum:
                    raise GenerationError("Не удалось получить нужное число уникальных записей; увеличьте справочники или измените параметры.")
                continue
            seen.add(key)
            people.append(person)
        return people

    def _one(self, identifier: int) -> Person:
        gender = self.rng.choices([Gender.MALE, Gender.FEMALE], weights=[self.config.male_percent, self.config.female_percent], k=1)[0]
        origin = choose_origin(self.rng, self.config.origins)
        dictionary = self.dictionaries[origin]
        return Person(identifier, self.rng.choice(dictionary.values("surname", gender)), self.rng.choice(dictionary.values("name", gender)), self.rng.choice(dictionary.values("patronymic", gender)), gender, random_birth_date(self.rng, self.config.min_date, self.config.max_date), generate_phone(self.rng, self.config.phone_prefix, self.config.phone_format), self.rng.choice(dictionary.cities), origin)


def statistics(people: list[Person]) -> Counter[str]:
    result: Counter[str] = Counter()
    for person in people:
        result[person.gender.value] += 1
        result[person.origin] += 1
    return result
