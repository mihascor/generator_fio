import csv
import json
from datetime import date
from pathlib import Path
from random import Random

import pytest

from fio_generator.birthdate import random_birth_date
from fio_generator.config import ConfigError, load_config
from fio_generator.declension import NameDeclensor
from fio_generator.exclusions import load_exclusions
from fio_generator.exporters import export_csv
from fio_generator.generator import PersonGenerator
from fio_generator.models import Gender, Person
from fio_generator.phone import generate_phone


ROOT = Path(__file__).parents[1]


def config_data(**changes):
    data = json.loads((ROOT / "config.example.json").read_text(encoding="utf-8"))
    for section, values in changes.items():
        data[section].update(values)
    return data


def write_config(tmp_path, data):
    (tmp_path / "data").symlink_to(ROOT / "data", target_is_directory=True)
    (tmp_path / "exclusions").mkdir()
    for name in ("names", "surnames", "patronymics", "cities"):
        (tmp_path / "exclusions" / f"{name}.txt").write_text("", encoding="utf-8")
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_config_and_cli_overrides(tmp_path):
    config = load_config(write_config(tmp_path, config_data()), {"count": 3, "seed": 10, "output": "result.csv"})
    assert config.generation.count == 3 and config.generation.seed == 10
    assert config.output_path == tmp_path / "result.csv"


def test_invalid_percentages(tmp_path):
    path = write_config(tmp_path, config_data(gender={"male_percent": 40, "female_percent": 40}))
    with pytest.raises(ConfigError, match="Сумма процентов"):
        load_config(path)


def test_date_range_and_leap_day():
    rng = Random(1)
    assert all(date(2024, 2, 28) <= random_birth_date(rng, date(2024, 2, 28), date(2024, 3, 1)) <= date(2024, 3, 1) for _ in range(30))
    assert random_birth_date(Random(2), date(2024, 2, 29), date(2024, 2, 29)) == date(2024, 2, 29)


def test_phone_template():
    phone = generate_phone(Random(3), "+7", "+7 (###) ###-##-##")
    assert phone.startswith("+7 (") and len([x for x in phone if x.isdigit()]) == 11


def test_exclusions_case_insensitive(tmp_path):
    (tmp_path / "names.txt").write_text(" иВАН \n", encoding="utf-8")
    result = load_exclusions(tmp_path, True)
    assert "иван" in result["names"]


def test_declension_male_and_female():
    dec = NameDeclensor()
    assert dec.decline_surname("Иванов", Gender.MALE, "genitive") == "Иванова"
    assert dec.decline_surname("Иванова", Gender.FEMALE, "instrumental") == "Ивановой"
    assert dec.decline_patronymic("Петрович", Gender.MALE, "dative") == "Петровичу"
    assert dec.decline_patronymic("Сергеевна", Gender.FEMALE, "genitive") == "Сергеевны"
    assert dec.decline_surname("Шевченко", Gender.MALE, "genitive") == "Шевченко"


def test_generation_distribution_origin_gender_seed_and_disabled_fields(tmp_path):
    data = config_data(generation={"count": 500, "seed": 42, "unique_records": False}, fields={"surname": True, "name": True, "patronymic": False, "full_name": False, "gender": False, "birth_date": False, "phone": False, "birth_city": False, "origin": False})
    path = write_config(tmp_path, data)
    config = load_config(path)
    from fio_generator.names import load_dictionaries
    generator = PersonGenerator(config, load_dictionaries(config.data_directory, {}))
    first = generator.generate()
    second = PersonGenerator(config, load_dictionaries(config.data_directory, {})).generate()
    assert first == second
    males = sum(p.gender == Gender.MALE for p in first)
    russia = sum(p.origin == "Russia" for p in first)
    assert 190 < males < 310 and 350 < russia < 450
    export_csv(first[:1], config)
    header = next(csv.reader(config.output_path.open(encoding="utf-8-sig"), delimiter=";"))
    assert header == ["id", "surname", "name"]


def test_csv_declension(tmp_path):
    data = config_data(generation={"count": 1, "seed": 1, "unique_records": False}, declension={"enabled": True, "case": "genitive"})
    config = load_config(write_config(tmp_path, data))
    person = Person(1, "Иванов", "Иван", "Петрович", Gender.MALE, date(2000, 1, 1), "+70000000000", "Москва", "Russia")
    export_csv([person], config)
    row = next(csv.DictReader(config.output_path.open(encoding="utf-8-sig"), delimiter=";"))
    assert row["surname_declined"] == "Иванова" and row["patronymic_declined"] == "Петровича"
