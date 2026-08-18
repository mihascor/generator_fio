"""Координация генерации записей."""

from __future__ import annotations

from collections import Counter
from random import Random
from typing import TypeVar

from .birthdate import random_birth_date
from .config import AppConfig
from .models import Gender, Person
from .names import OriginDictionary
from .phone import generate_phone


DistributionValue = TypeVar("DistributionValue")


class GenerationError(RuntimeError):
    """Запрошенная уникальная выборка не может быть построена."""


class PersonGenerator:
    """Генератор с собственным RNG для воспроизводимых результатов."""

    def __init__(self, config: AppConfig, dictionaries: dict[str, OriginDictionary]) -> None:
        self.config, self.dictionaries = config, dictionaries
        self.rng = Random(config.generation.seed)

    def generate(self) -> list[Person]:
        genders = self._distributed_values(
            ((Gender.MALE, self.config.male_percent), (Gender.FEMALE, self.config.female_percent))
        )
        origins = self._distributed_values(tuple(self.config.origins.items()))
        people: list[Person] = []
        seen: set[tuple[object, ...]] = set()
        attempts, maximum = 0, max(self.config.generation.count * 100, 1000)
        while len(people) < self.config.generation.count:
            index = len(people)
            person = self._one(index + 1, genders[index], origins[index])
            key = (person.surname, person.name, person.patronymic, person.gender, person.birth_date, person.phone, person.birth_city, person.origin)
            if self.config.generation.unique_records and key in seen:
                attempts += 1
                if attempts >= maximum:
                    raise GenerationError("Не удалось получить нужное число уникальных записей; увеличьте справочники или измените параметры.")
                continue
            seen.add(key)
            people.append(person)
        return people

    def _distributed_values(self, percentages: tuple[tuple[DistributionValue, int], ...]) -> list[DistributionValue]:
        """Вернуть перемешанный набор с количеством, ближайшим к заданным долям."""
        count = self.config.generation.count
        quotas = [(value, count * percent // 100, count * percent % 100) for value, percent in percentages]
        remaining = count - sum(quota for _, quota, _ in quotas)
        # Метод наибольших остатков: лишние записи получают наибольшие дробные части.
        extras = {index for index, _ in sorted(enumerate(quotas), key=lambda item: item[1][2], reverse=True)[:remaining]}
        values = [value for index, (value, quota, _) in enumerate(quotas) for _ in range(quota + (index in extras))]
        self.rng.shuffle(values)
        return values

    def _one(self, identifier: int, gender: Gender, origin: str) -> Person:
        dictionary = self.dictionaries[origin]
        return Person(identifier, self.rng.choice(dictionary.values("surname", gender)), self.rng.choice(dictionary.values("name", gender)), self.rng.choice(dictionary.values("patronymic", gender)), gender, random_birth_date(self.rng, self.config.min_date, self.config.max_date), generate_phone(self.rng, self.config.phone_prefix, self.config.phone_format), self.rng.choice(dictionary.cities), origin)


def statistics(people: list[Person]) -> Counter[str]:
    result: Counter[str] = Counter()
    for person in people:
        result[person.gender.value] += 1
        result[person.origin] += 1
    return result
