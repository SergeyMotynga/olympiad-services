# Как проверить сервис доступа

## Вход и создание аккаунтов

1. Заполни `.env` по [инструкции запуска](../../../README.md#локальный-запуск). Затем из корня запусти `docker compose up --build --wait`.
2. Создай первого администратора. Скрипт попросит пароль в терминале.

   ```sh
   docker compose exec access python -m olympiad_access.bootstrap --login first.admin
   ```

3. Открой [Swagger](http://127.0.0.1:8001/docs). В `POST /auth/login` введи логин и пароль администратора. Скопируй `access_token` из ответа и вставь его в **Authorize**.
4. Выполни `GET /roles` и возьми `id` нужной роли, например `author`. Выполни `POST /accounts` с логином `demo.author`, паролем и числовым `role_id`. В ответе будут ID аккаунта, нормализованный логин и `role_id`. Для смены роли передай новый `role_id` в `PATCH /accounts/{account_id}/role`.
5. Войди дважды под созданным аккаунтом. Авторизуй первый токен и выполни `POST /auth/logout`. Первый токен становится недействительным. Второй можно использовать для отдельного выхода.

## Проверка доступа между сервисами

Контракт `CheckAccess` находится в [access.proto](../../../backend/contracts/src/olympiad_contracts/access.proto). В сети Docker Compose адрес сервиса — `access:50051`. Сервис принимает токен и код операции. При разрешении результат включает UUID аккаунта. При отказе поле идентификатора пустое.

| Роль | Операции |
|---|---|
| Администратор | Все перечисленные gRPC-операции, включая `tasks:print` и `submissions:open`. Через HTTP API создаёт аккаунты и назначает роли. |
| Составитель заданий | `tasks:list`, `tasks:create`, `tasks:update`. |
| Представитель | `submissions:list`, `submissions:create`, `submissions:update`. |
| Проверяющий | Может войти в систему. Операции проверки ответов появятся на этапе реализации проверки. |

## Интеграционные тесты

Тестовый PostgreSQL поднимается отдельно и слушает только на локальном порту `55432`. Тесты применяют миграции к базе `access_test`.

```powershell
docker compose -f compose.access-test.yaml up -d --wait
$env:ACCESS_TEST_DATABASE_URL = 'postgresql+asyncpg://access_test_app:access_test@127.0.0.1:55432/access_test'
Set-Location backend
uv run --locked --all-packages --group codegen python generate_contracts.py
uv run --locked --all-packages pytest
```

Из корня репозитория `docker compose -f compose.access-test.yaml down` останавливает тестовую БД.
