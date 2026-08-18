"""Работа с группами происхождения и городами."""

from random import Random


def choose_origin(rng: Random, origins: dict[str, int]) -> str:
    names, weights = zip(*origins.items())
    return rng.choices(names, weights=weights, k=1)[0]
