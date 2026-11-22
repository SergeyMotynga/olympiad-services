# Olympiad Services

Сервисы математических игр. Назначение приложений и стек описаны в [спецификации](docs/specification.md).

## Локальный запуск

Скопируй [`.env.example`](.env.example) в `.env` в корне и заполни четыре пароля PostgreSQL. Compose читает `.env`, Git игнорирует его. Пароли со знаками `$` или `#` заключай в одинарные кавычки. Для существующего Docker-тома значения должны совпадать с паролями созданных ролей.

Из корня репозитория выполни команду с работающим Docker Compose.

```sh
docker compose up --build --wait
```

Compose поднимает три приложения и PostgreSQL. При первом запуске PostgreSQL создаёт для каждого приложения отдельную базу и роль. Перед запуском HTTP каждое приложение применяет свои миграции Alembic. Python и зависимости устанавливаются внутри Docker-образов.

| Сервис | Проверка готовности | OpenAPI |
|---|---|---|
| Доступ и роли | [порт 8001](http://127.0.0.1:8001/ready) | [Swagger UI](http://127.0.0.1:8001/docs) |
| Задачи и печать | [порт 8002](http://127.0.0.1:8002/ready) | [Swagger UI](http://127.0.0.1:8002/docs) |
| Приём бланков | [порт 8003](http://127.0.0.1:8003/ready) | [Swagger UI](http://127.0.0.1:8003/docs) |

`GET /ready` возвращает `200` и `{"status": "ready"}`, когда приложение может выполнить запрос к своей базе. Если база недоступна, ответ содержит `503` и `{"status": "not_ready"}`.

Команда `docker compose ps` показывает состояние контейнеров, а `docker compose down` останавливает их с сохранением данных. PostgreSQL доступен внутри сети Compose. Учётные данные для локального запуска хранятся в `.env`.

[Проверка сервиса доступа в Swagger](docs/backend/access/review.md)

## Проверки бэкенда

Если локально уже установлен `uv`, запусти из каталога `backend/`.

```sh
uv run --locked --all-packages --group codegen python generate_contracts.py
uv run --locked --all-packages pytest
uv run --locked --all-packages ruff check .
uv run --locked --all-packages ruff format --check .
uv run --locked --all-packages mypy .
```

Тесты `/ready` в `backend/tests/` направляют приложения на недоступный адрес и проверяют ответ `503`. GitHub Actions также запускает Compose в отдельном окружении со свежим томом PostgreSQL. Эта проверка запускает миграции и ждёт готовности всех трёх сервисов. Интеграционные тесты доступа используют отдельную базу по адресу ACCESS_TEST_DATABASE_URL. [Как запустить тестовую БД](docs/backend/access/review.md#интеграционные-тесты).

## Как устроен бэкенд

- `backend/services/` содержит три приложения. У каждого свой Python-пакет и каталог ревизий Alembic.
- `backend/runtime/` содержит общий код запуска FastAPI, настройки подключения к PostgreSQL и обработчик `/ready`.
- `backend/postgres/init.sql` создаёт базы и роли при инициализации пустого тома. Дальнейшие изменения схемы каждого сервиса выполняет Alembic.

В Compose один контейнер из образа `postgres:17-alpine`. Внутри него один сервер PostgreSQL обслуживает три отдельные базы: `access`, `tasks_print` и `submissions`. Каждый сервис получает `DATABASE_NAME`, `DATABASE_USER` и `DATABASE_PASSWORD` для подключения к своей базе.
