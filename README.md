# Генератор ФИО

Локальная Python-программа для массового создания тестовых персональных данных: ФИО, пола, даты и города рождения, телефона и источника справочника (`Russia`/`CIS`). Внешние API не используются.

## Установка

Нужен Python 3.11 или новее.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Для shell `fish` (часто выбран в терминале VS Code на Linux):

```fish
source .venv/bin/activate.fish
```

```bash
pip install -r requirements.txt
```

## Запуск

```bash
python -m fio_generator --config config.example.json
python -m fio_generator --config config.example.json --count 10000 --output output/test.csv --seed 123
```

Параметры `--count`, `--output` и `--seed` имеют приоритет над JSON. `--help` выводит полную справку. Результат по умолчанию — CSV с разделителем `;` и кодировкой `utf-8-sig`, удобной для Excel.

## Конфигурация

`generation` задаёт число строк, seed (или `null`) и требование полной уникальности записи. `fields` включает колонки; `full_name` собирается из включённых частей ФИО и может быть отключён. `gender` и `origin` содержат проценты, каждая сумма обязана быть 100.

`birth_date` содержит включительный диапазон ISO-дат и формат вывода. `phone` использует шаблон: каждый `#` заменяется цифрой, а число `#` должно совпадать с `digits_after_prefix`. Например, `+7 (###) ###-##-##`.

`declension.enabled` добавляет исходные и склонённые колонки; допустимые падежи: `nominative`, `genitive`, `dative`, `accusative`, `instrumental`, `prepositional`. Склоняются типовые русские фамилии и отчества, а заведомо несклоняемые фамилии сохраняются.

Все относительные пути (`data_directory`, `exclusions.directory`, `output.path`) разрешаются от каталога JSON-файла. Ошибки схемы, пустых и отсутствующих справочников выводятся в читаемом виде.

## Справочники и исключения

Справочники лежат в `data/russia` и `data/cis`; в каждом каталоге требуются файлы `male_names.txt`, `female_names.txt`, `male_surnames.txt`, `female_surnames.txt`, `male_patronymics.txt`, `female_patronymics.txt`, `cities.txt`. По одному значению в строке. Пустые строки и дубли игнорируются. Новые каталоги можно добавлять в загрузчик без изменения генератора; для выбора новой группы нужно добавить её процент в конфигурацию.

В `exclusions/names.txt`, `surnames.txt`, `patronymics.txt`, `cities.txt` укажите исключаемые значения построчно. Регистр и пробелы по краям не учитываются. Фильтрация происходит один раз при загрузке справочников.

## Проверка

```bash
pytest
```

## Очистка и сортировка справочника

Утилита `scripts/sort_dictionary.py` сортирует файл по алфавиту, удаляет
пустые строки и дубли (без учёта регистра), затем заменяет исходный файл.

```bash
python scripts/sort_dictionary.py data/russia/cities.txt
```

В `fish`, если виртуальное окружение активно, можно использовать ту же команду
`python`; либо запустить напрямую `.venv/bin/python scripts/sort_dictionary.py data/russia/cities.txt`.
