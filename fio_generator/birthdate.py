"""Генерация календарно корректных дат."""

from datetime import date, timedelta
from random import Random


def random_birth_date(rng: Random, min_date: date, max_date: date) -> date:
    """Вернуть равновероятную дату из включительного диапазона."""
    return min_date + timedelta(days=rng.randint(0, (max_date - min_date).days))
