"""Доменные модели приложения."""

from dataclasses import dataclass
from datetime import date
from enum import Enum


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"


@dataclass(frozen=True)
class Person:
    """Одна сгенерированная запись."""

    id: int
    surname: str
    name: str
    patronymic: str
    gender: Gender
    birth_date: date
    phone: str
    birth_city: str
    origin: str
