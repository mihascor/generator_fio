"""Командный интерфейс."""

import argparse
import logging

from .config import ConfigError, load_config
from .exclusions import load_exclusions
from .exporters import export_csv
from .generator import GenerationError, PersonGenerator, statistics
from .names import DictionaryError, load_dictionaries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Генератор ФИО и локальных персональных данных в CSV.")
    parser.add_argument("--config", required=True, help="Путь к JSON-конфигурации.")
    parser.add_argument("--count", type=int, help="Количество записей (перекрывает JSON).")
    parser.add_argument("--output", help="Путь к CSV (перекрывает JSON).")
    parser.add_argument("--seed", type=int, help="Seed генератора (перекрывает JSON).")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        config = load_config(args.config, vars(args))
        dictionaries = load_dictionaries(config.data_directory, load_exclusions(config.exclusions_directory, config.exclusions_enabled))
        people = PersonGenerator(config, dictionaries).generate()
        path = export_csv(people, config)
    except (ConfigError, DictionaryError, GenerationError, OSError, ValueError) as error:
        logging.error("%s", error)
        return 2
    result = statistics(people)
    print(f"Generated: {len(people)}\nМуж: {result['Муж']}\nЖен: {result['Жен']}\nRussia: {result['Russia']}\nCIS: {result['CIS']}\nOutput: {path}")
    return 0
