# Архитектура

Минимальный стек для потоковой обработки данных строится вокруг трёх слоёв: источники данных, обработка по стадиям и инфраструктура для событий/артефактов.

## Поток данных
```
StreamHandler → CollectorService → PredictorService → EventBus → (Artifacts + DB)
```
1. **StreamHandler** — источник данных. В демо это `DummyStreamHandler`, генерирующий синтетические кадры.
2. **CollectorService** — превращает батч кадров в список `PredictionInput` для стадий.
3. **PredictorService** — диспетчер по `PredictionStage`, запускает нужный предиктор и отдаёт `PredictionOutcome`.
4. **EventBus** — Pub/Sub для событий `PredictionCompleted` и др. Сейчас используется in-memory реализация.
5. **ArtifactPersistence + SQLite** — сохраняют артефакты и запись о предсказании.

## Ключевые компоненты
- `configs/settings.py` — загрузка путей и окружения из `.env` (`MMLA_*`).
- `application/cases/*` — манифесты, bootstrap и фабрики кейсов. `CaseBuildContext` прокидывает зависимости (event bus, репозиторий, стореджи).
- `application/orchestrator.py` — связывает стрим, коллектор и предикторы, публикует события.
- `core/domain/*` — value objects, события, модели данных (`PredictionStage`, `PredictionOutcome` и т.д.).
- `implementations/examples/dummy/*` — пример handler/predictor/config для кейса `dummy_offline`.
- `infrastructure/*` — in-memory event bus, локальное хранилище файлов и артефактов, SQLite-репозиторий.

## Добавление нового кейса
1. Создайте `samples/<slug>/case.yaml` и `blueprint.py`.
2. Опишите pydantic-модели манифеста и экспортируйте `make_blueprint(context)`.
3. Зарегистрируйте модуль в `application/cases/factories.py::BLUEPRINT_MODULES`.
4. Реализуйте `StreamHandler`, функции коллектора и предикторы для нужных стадий.
5. Запустите CLI: `python cli.py list` → `python cli.py run <slug>`.

