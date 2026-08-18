"""Шаблонный генератор телефонных номеров."""

from random import Random


def generate_phone(rng: Random, prefix: str, pattern: str) -> str:
    """Заменить каждый # в шаблоне случайной цифрой; prefix проверяется конфигом."""
    generated = "".join(str(rng.randrange(10)) if char == "#" else char for char in pattern)
    return generated if generated.startswith(prefix) else prefix + generated
