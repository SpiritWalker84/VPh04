# VPh04: Nginx + FastAPI + PostgreSQL + pgAdmin

## Краткое описание

**Что делает.** Контейнерный стек для приёма **заявок лидов** и **админ-каталога услуг**: **FastAPI** (async SQLAlchemy, Alembic) ходит в **PostgreSQL**; снаружи доступен только **Nginx** (`/api/` → backend), порт **8000** контейнера на хост **не публикуется**. **Админка `/admin/`** после входа использует сессионную cookie (учётные данные из `.env`). **Swagger / OpenAPI** (`/api/docs`) включаются только при **`DOCS_ENABLED=true`** (в обычном подъёме через Compose по умолчанию выключены). **pgAdmin** — для администрирования БД.

**Как запускать.** Из корня: `cp .env.example .env` (пароли, при необходимости порты), затем `docker compose up -d --build` — образ **nginx** собирает фронтенд внутри себя. Логи: `docker compose logs -f backend` / `nginx` / `postgres`. Остановка: `docker compose down`.

**HTTP и TLS.** По умолчанию — **HTTP** (без TLS), как в текущем ТЗ. **Без HTTPS** cookie сессии админки уходит по сети открытым текстом; для публичного доступа имеет смысл поставить TLS (reverse proxy) и включить у cookie флаг Secure в приложении. HTTPS настраивается отдельно на стороне Nginx или внешнего балансировщика.

**Ограничения:** один общий логин/пароль админки из окружения; данные БД — в volume `postgres_data`.

Структура и оформление согласованы с [Guide](https://github.com/SpiritWalker84/Guide) (`docs/conventions/`).

## Стек

- **Backend:** Python **3.12**, **FastAPI**, **Uvicorn**, **SQLAlchemy 2** (async, **asyncpg**), **Alembic** (миграции через **psycopg** v3), **Pydantic v2** / **pydantic-settings**
- **Frontend:** **Vite 6**, **TypeScript** (strict), **чистый CSS** (токены, без UI-фреймворка), MPA: `/` и `/admin/`
- **Инфра:** Docker / Docker Compose v2, **Nginx** 1.27 (Alpine), **PostgreSQL** 16 (Alpine), **pgAdmin 4**

## Структура

| Путь | Назначение |
|------|------------|
| `backend/app/` | FastAPI: `main`, `config`, `core/database`, `models`, `schemas`, `repositories`, `services`, `api/v1` |
| `backend/alembic/` | Миграции БД |
| `backend/Dockerfile` | Сборка образа: `alembic upgrade head` + `uvicorn` |
| `docker/web/Dockerfile` | Multi-stage: Node-сборка фронта → nginx со встроенной статикой |
| `docker-compose.yml` | `postgres`, `pgadmin`, `nginx` (образ `vph04-web`), `backend` |
| `frontend/` | Исходники UI; прод-статика попадает в образ nginx при `docker compose build` |
| `docker/nginx/conf.d/default.conf` | Копируется в образ web: `/api/` → backend, `/admin/` |
| `.env.example` | Шаблон окружения |
| `.gitignore` | `.env`, Python-служебные файлы |

### API (префикс `/api/v1`)

| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/api/v1/health` | Проверка живости |
| GET/POST | `/api/v1/applications` | Список / создание заявки (опционально вложенный блок `behavior`) |
| GET | `/api/v1/applications/{id}` | Заявка по id |
| GET | `/api/v1/admin/settings` | Активные услуги (для формы) |
| POST | `/api/v1/auth/login` | Вход админки (тело JSON `username`, `password`; выставляет cookie) |
| POST | `/api/v1/auth/logout` | Выход (очистка сессии) |
| GET | `/api/v1/auth/me` | Флаг `authenticated` для текущей сессии |
| GET | `/api/v1/admin/settings/all` | Все записи справочника (**только с сессией админа**) |
| POST | `/api/v1/admin/settings` | Добавить услугу/диапазон бюджета (**с сессией**) |
| PATCH | `/api/v1/admin/settings/{id}` | Обновить (**с сессией**) |
| DELETE | `/api/v1/admin/settings/{id}` | Удалить (**с сессией**) |

Документация OpenAPI: **`http://localhost:8080/api/docs`** — только если в `.env` задано **`DOCS_ENABLED=true`** (порт хоста — `NGINX_HTTP_PORT`).

## Запуск

### Docker Compose (основной способ)

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
```

Образ **nginx** (`vph04-web`) собирает фронтенд внутри multi-stage Dockerfile; отдельный **`npm run build` на хосте не нужен** для запуска через Compose. Для локальной разработки UI по-прежнему удобен **`npm run dev`** в `frontend/`.

После изменений **только фронта:** пересоберите web-образ: `docker compose build nginx && docker compose up -d nginx` (или `docker compose up -d --build`).

Проверка:

- Клиентская форма: `http://localhost:8080/`
- Админ-каталог: `http://localhost:8080/admin/`
- Health: `http://localhost:8080/api/v1/health`
- Swagger (если `DOCS_ENABLED=true`): `http://localhost:8080/api/docs`
- pgAdmin: `http://localhost:5050/`

### pgAdmin: сервер PostgreSQL

**Connection:** Host `postgres`, Port `5432`, учётные данные из `.env` (`POSTGRES_*`). Логин в pgAdmin — `PGADMIN_DEFAULT_EMAIL` (не используйте зону `.local`).

### Локальная разработка frontend (`vite`)

При запущенном стеке Compose запросы к **`/api`** проксируются на `http://127.0.0.1:8080` (Nginx → backend).

```bash
cd frontend
npm install
npm run dev
```

Открыть **`http://127.0.0.1:5173/`** (клиент) и **`http://127.0.0.1:5173/admin/`** (админ).

### Локальная разработка backend (без пересборки образа)

Нужен свой **DATABASE_URL** в `.env` (async, например `postgresql+asyncpg://…`) и доступ к Postgres по TCP. Для сессии админки задайте **`SECRET_KEY`** (≥ 32 символов), **`ADMIN_USERNAME`**, **`ADMIN_PASSWORD`**.

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+asyncpg://...
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Проверка Compose

```bash
docker compose config
```

## Конфигурация

| Переменная | Обязательность | Описание |
|------------|----------------|----------|
| `POSTGRES_USER` | да | Пользователь БД |
| `POSTGRES_PASSWORD` | да | Пароль БД |
| `POSTGRES_DB` | да | Имя базы |
| `PGADMIN_DEFAULT_EMAIL` | да | Логин pgAdmin |
| `PGADMIN_DEFAULT_PASSWORD` | да | Пароль pgAdmin |
| `NGINX_HTTP_PORT` | нет | Порт хоста → HTTP (по умолчанию `8080`) |
| `PGADMIN_PORT` | нет | Порт хоста → pgAdmin (по умолчанию `5050`) |
| `DATABASE_URL` | нет в Compose | Задаётся в `docker-compose` для `backend`; для локального uvicorn — в `.env` |
| `SECRET_KEY` | да (в Compose) | Случайная строка ≥ 32 символов; подпись cookie сессии |
| `ADMIN_USERNAME` | нет | Логин админки (по умолчанию `admin`) |
| `ADMIN_PASSWORD` | да | Пароль админки (≥ 8 символов) |
| `DOCS_ENABLED` | нет | `true` / `false` — OpenAPI UI и схема (по умолчанию `false`) |

`DATABASE_URL` в Docker: `postgresql+asyncpg://…` (см. `docker-compose.yml`).

Локально при `uvicorn` задайте те же `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, что и для рабочей среды, иначе сессия не будет совпадать с Docker.

## Разработка и тесты

```bash
docker compose config
docker compose logs -f backend
python3 -m compileall -q backend/app
```

При расширении проекта — `pytest`, `ruff`/`mypy` по необходимости.
