# MMLA Framework
# (Modular Machine Learning Architecture)

Универсальный каркас для потоковой обработки данных (видео, датчики и т.п.) с явной декомпозицией на обработчики потоков, коллекторы и предикторы. В репозитории есть несколько демонстрационных кейсов, работающих на синтетических данных.

## Преимущества
- **Минимальные зависимости.** In-memory event bus, локальное файловое хранилище и SQLite — всё можно заменить своими адаптерами через `CaseBuildContext`.
|- **Плагинные кейсы.** Каждый кейс изолирован в `samples/<slug>` и подключается одной строкой в `BLUEPRINT_MODULES`.
- **Простая схема стадий.** `PredictionStage` ограничен валидацией и аналитикой; регистрируешь предикторы по ключу — получаешь последовательную обработку.
- **Чистые модели.** Pydantic-конфиги, value objects и доменные события без привязки к конкретному домену.


## Ключевые идеи
- **Плагинные кейсы.** Каждый кейс лежит в `samples/<slug>` и описан манифестом `case.yaml` и модулем `blueprint.py`. Бутстрап находит манифесты и регистрирует фабрики кейсов.
- **Явные этапы обработки.** Предикторы регистрируются по стадиям (`PredictionStage`), оркестратор исполняет их по очереди для каждой сессии.
- **Простая интеграция.** Минимальный набор инфраструктуры: in-memory event bus, локальное хранилище артефактов, SQLite-персистенция. Всё заменяемо через зависимости в `CaseBuildContext`.
- **Чистое API.** Pydantic-модели конфигурации, value objects и интерфейсы позволяют быстро добавлять новые кейсы.

## Структура
| Путь                | Назначение                                                                                          |
|---------------------|-----------------------------------------------------------------------------------------------------|
| `application/`      | Оркестратор кейсов, bootstrap, runtime, работа с артефактами.                                       |
| `core/`             | Доменные модели, события, value objects, интерфейсы.                                                |
| `configs/`          | Настройки (`AppSettings`) и загрузка из `.env` (`MMLA_*`).                                           |
| `implementations/`  | Примерные обработчики/предикторы (`examples/dummy`, `examples/vision`).                             |
| `samples/`          | Манифесты и blueprints кейсов (`dummy_offline`, `yolov8_detection`, `resnet50_classification`, `threshold_alert`). |
| `infrastructure/`   | In-memory event bus, локальные стореджи, SQLite-репозиторий.                                        |
| `tests/`            | Проверка CLI и демо-кейсов.                                                                         |
| `docs/`             | Архитектура и примеры создания кейсов.                                                             |

## Установка
```bash
python -m venv .venv
.venv\Scripts\activate  # или source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env  # настройте пути при необходимости
```

В `.env` можно указать `MMLA_CASES_ROOT`, `MMLA_MODELS_ROOT`, `MMLA_ARTIFACTS_ROOT`, `MMLA_DATA_ROOT`, `MMLA_DATABASE_PATH`, `MMLA_MANIFEST_NAME`. По умолчанию пути относительны к корню репозитория.

## Быстрый старт
Список кейсов:
```bash
python cli.py list
```

Запуск демо на 5 секунд:
```bash
python cli.py run dummy_offline --duration 5
```

Переопределение серийников и метаданных:
```bash
python cli.py run dummy_offline --device-serial dummy_offline=dev123 --metadata dummy_offline:location=lab
```

## Как добавить свой кейс
1. Создайте папку `samples/<slug>` с `case.yaml` (манифест) и `blueprint.py` (фабрика).
2. В `application/cases/factories.py` добавьте модуль в `BLUEPRINT_MODULES` либо используйте автосканы.
3. Опишите `make_blueprint(context)`, зарегистрируйте предикторы по стадиям и свой `StreamHandler`/`Collector`.
4. Запустите `python cli.py list`, убедитесь, что кейс виден, затем `python cli.py run <slug>`.
5. Подробный пример — в `docs/CASE_EXAMPLE.md`.

## Тесты
```bash
pytest -q
```

## Документация
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — обзор компонентов и потока данных.
- [docs/CASE_EXAMPLE.md](docs/CASE_EXAMPLE.md) — пошаговый пример добавления кейса `threshold_alert`.

## Демонстрационные кейсы
- `dummy_offline` — синтетические кадры, валидация + аналитика.
- `yolov8_detection` — синтетические кадры + демонстрационный детектор (YOLOv8-style).
- `resnet50_classification` — синтетические кадры + демонстрационная классификация (ResNet50-style).
- `threshold_alert` — синтетические кадры + алерт по среднему значению пикселей.
