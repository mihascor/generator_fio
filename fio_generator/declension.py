"""Изолированные предсказуемые правила склонения русских фамилий и отчеств.

Модуль намеренно имеет простой интерфейс, чтобы позднее его можно было заменить
морфологической библиотекой без изменений генератора.
"""

from .models import Gender


class NameDeclensor:
    """Склоняет типовые русские фамилии и отчества."""

    _CASES = {"nominative", "genitive", "dative", "accusative", "instrumental", "prepositional"}

    def decline_surname(self, value: str, gender: Gender, case: str) -> str:
        self._validate(case)
        if case == "nominative" or self._indeclinable(value):
            return value
        stem, ending = self._surname_stem(value, gender)
        if ending is None:
            return value
        endings = {
            "male_consonant": {"genitive": "а", "dative": "у", "accusative": "а", "instrumental": "ым", "prepositional": "е"},
            "male_iy": {"genitive": "ого", "dative": "ому", "accusative": "ого", "instrumental": "им", "prepositional": "ом"},
            "female_a": {"genitive": "ой", "dative": "ой", "accusative": "у", "instrumental": "ой", "prepositional": "ой"},
            "female_aya": {"genitive": "ой", "dative": "ой", "accusative": "ую", "instrumental": "ой", "prepositional": "ой"},
        }
        return stem + endings[ending][case]

    def decline_patronymic(self, value: str, gender: Gender, case: str) -> str:
        self._validate(case)
        if case == "nominative":
            return value
        lower = value.casefold()
        if gender == Gender.MALE and lower.endswith(("ич", "ыч")):
            endings = {"genitive": "а", "dative": "у", "accusative": "а", "instrumental": "ем", "prepositional": "е"}
            return value + endings[case]
        if gender == Gender.FEMALE and lower.endswith("на"):
            endings = {"genitive": "ы", "dative": "е", "accusative": "у", "instrumental": "ой", "prepositional": "е"}
            return value[:-1] + endings[case]
        return value

    @staticmethod
    def _indeclinable(value: str) -> bool:
        return value.casefold().endswith(("ко", "енко", "их", "ых", "о", "е", "и", "у", "ю"))

    @staticmethod
    def _surname_stem(value: str, gender: Gender) -> tuple[str, str | None]:
        lower = value.casefold()
        if gender == Gender.FEMALE and lower.endswith("ая"):
            return value[:-2], "female_aya"
        if gender == Gender.FEMALE and lower.endswith("а"):
            return value[:-1], "female_a"
        if gender == Gender.MALE and lower.endswith(("ий", "ый")):
            return value[:-2], "male_iy"
        if gender == Gender.MALE and lower[-1:] in "бвгджзйклмнпрстфхцчшщ":
            return value, "male_consonant"
        return value, None

    def _validate(self, case: str) -> None:
        if case not in self._CASES:
            raise ValueError(f"Неизвестный падеж: {case}")
