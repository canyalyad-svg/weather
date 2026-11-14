# Chat Assistant (Mistral Workflow)

Многошаговый чат-ассистент в виде [Mistral Workflow](https://docs.mistral.ai/studio/workflows/): работает в чате Vibe Work, помнит контекст диалога и отвечает через модель `mistral-medium-latest`.

## Как это работает

- Workflow `chat-assistant` принимает сообщения пользователя через `ChatInput` и пересылает их агенту (`Agent` + `RemoteSession(stream=True)`), который сохраняет контекст беседы.
- Команды `стоп` / `stop` / `выход` / `пока` завершают диалог.
- Воркер запускается командой `python -m worker.entrypoints.worker` и регистрирует все workflow из `worker.workflows`.

## Структура

```
Dockerfile.worker          # образ для managed-деплоя
src/worker/workflows/      # код workflow
src/worker/entrypoints/    # точка входа воркера
tests/                     # тесты (pytest + temporal test env)
```

## Локальная разработка

```bash
uv sync
uv run pytest
```

Для запуска воркера локально нужен `MISTRAL_API_KEY` в `.env`:

```bash
uv run python -m worker.entrypoints.worker
```

## Деплой

Деплой выполняется как managed deployment из этого репозитория (Dockerfile: `Dockerfile.worker`). Ключи API не нужны: воркер аутентифицируется сервисным токеном платформы.
