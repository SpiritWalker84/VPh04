# VPh04: Nginx + FastAPI + PostgreSQL

## Краткое описание

**Что делает.** Контейнерный стек для приёма **заявок лидов** и **админ-каталога услуг**: **FastAPI** (async SQLAlchemy, Alembic) ходит в **PostgreSQL**; снаружи доступен только **Nginx** (`/api/` → backend), порт **8000** контейнера на хост **не публикуется**. Заявки при создании получают **оценку приоритета (балл и «температура» лид)** — логика на backend. **Админка `/admin/`**: **JWT** (Bearer), первый администратор создаётся через **`GET /api/v1/auth/check`** + форму регистрации, учётные записи и **bcrypt-хеши** в таблице **`admins`**. В интерфейсе админки по умолчанию открыт **каталог услуг**; раздел **«Сводка заявок»** (дашборд + таблица с сортировкой **по приоритету** или **по дате**) подгружает данные **при переходе в этот раздел**, а не сразу после входа (объём строк за один запрос к API — параметр **`limit`**, не более **200**; в текущем клиенте по умолчанию **100**). **Swagger / OpenAPI** (`/api/docs`) включаются только при **`DOCS_ENABLED=true`** (в обычном подъёме через Compose по умолчанию выключены).

**Как запускать.** Из корня: `cp .env.example .env` (пароли, при необходимости порты), затем `docker compose up -d --build` — образ **nginx** собирает фронтенд внутри себя. Логи: `docker compose logs -f backend` / `nginx` / `postgres`. Остановка: `docker compose down`. Сервис **pgAdmin** из compose убран; при необходимости работайте с БД через `docker compose exec postgres psql …`, клиент на хосте с проброшенным портом (отдельно) или временно добавьте pgAdmin в compose.

**HTTP и TLS.** По умолчанию — **HTTP** (без TLS). **JWT** в браузере хранится в `localStorage`; при работе по HTTPS имеет смысл снижать риск XSS и при необходимости переносить токен в httpOnly-cookie. HTTPS настраивается отдельно на стороне Nginx или внешнего балансировщика.

**Ограничения:** учётные записи админов в БД; расширенный CRUD по нескольким админам можно добавить отдельно.

## Что доступно снаружи (типовой Compose)

В **`docker-compose.yml`** на **хост** (сеть машины, где запущен Docker) проброшен **только HTTP-порт сервиса `nginx`** — `NGINX_HTTP_PORT` → контейнерный **80** (по умолчанию **8080**). Через него отдаются сайт, админка и префикс **`/api/`**.

**Не публикуются и снаружи недоступны:**

- **Backend** (Uvicorn / FastAPI) — только внутри сети Compose; клиенты ходят в API **через Nginx**, а не напрямую на порт приложения.
- **PostgreSQL** — порт **`5432`** на хост **не открыт**; подключение из контейнера или через `docker compose exec` (см. ниже).
- **pgAdmin** и прочие вспомогательные сервисы **в compose не подключены**; при желании их нужно добавить отдельно и явно решить вопрос публикации портов.

Итого: на **хосте** из внешних по отношению к стеку сервисов обычно открыт **только порт Nginx**; **отдельные порты бэкенда, PostgreSQL и pgAdmin в стандартном compose наружу не выставлены** — API и UI идут через единый HTTP-вход.

Структура и оформление согласованы с [Guide](https://github.com/SpiritWalker84/Guide) (`docs/conventions/`).

## Стек

- **Backend:** Python **3.12**, **FastAPI**, **Uvicorn**, **SQLAlchemy 2** (async, **asyncpg**), **Alembic** (миграции через **psycopg** v3), **Pydantic v2** / **pydantic-settings**
- **Frontend:** **Vite 6**, **TypeScript** (strict), **чистый CSS** (токены, без UI-фреймворка), MPA: `/` и `/admin/`
- **Инфра:** Docker / Docker Compose v2, **Nginx** 1.27 (Alpine), **PostgreSQL** 16 (Alpine)

## Структура

| Путь | Назначение |
|------|------------|
| `backend/app/` | FastAPI: `main`, `config`, `core/database`, `models`, `schemas`, `repositories`, `services`, `api/v1` |
| `backend/alembic/` | Миграции БД |
| `backend/Dockerfile` | Сборка образа: `alembic upgrade head` + `uvicorn` |
| `docker/web/Dockerfile` | Multi-stage: Node-сборка фронта → nginx со встроенной статикой |
| `docker-compose.yml` | `postgres`, `nginx` (образ `vph04-web`), `backend` |
| `frontend/` | Исходники UI; прод-статика попадает в образ nginx при `docker compose build` |
| `docker/nginx/conf.d/default.conf` | Копируется в образ web: `/api/` → backend, `/admin/` |
| `backend/sql/admins_table.sql` | Ручной DDL таблицы `admins` (дублирует миграцию Alembic) |
| `.env.example` | Шаблон окружения |
| `.gitignore` | `.env`, Python-служебные файлы |

### API (префикс `/api/v1`)

| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/api/v1/health` | Проверка живости |
| POST | `/api/v1/applications` | Создание заявки (публично); опционально вложенный `behavior` |
| GET | `/api/v1/applications` | Список заявок для админки (**JWT**); `limit`, `skip`, `sort`: `priority` \| `recent` |
| GET | `/api/v1/applications/dashboard` | Сводка по заявкам для дашборда (**JWT**) |
| GET | `/api/v1/applications/{id}` | Заявка с полями и контактами для карточки (**JWT**) |
| POST | `/api/v1/behavior-metrics` | Приём анонимных метрик лендинга (время на странице, клики, курсор и т.д.) |
| GET | `/api/v1/behavior-metrics/stats` | Агрегаты и хитмап для модалки «Статистика» (**JWT**) |
| GET | `/api/v1/behavior-metrics` | Выборка сырых записей потока (**JWT**, при необходимости отладки) |
| GET | `/api/v1/admin/settings` | Активные услуги (для формы) |
| GET | `/api/v1/auth/check` | Публично: `registration_open` — показывать ли первую регистрацию |
| POST | `/api/v1/auth/register` | Первый админ (только пока таблица `admins` пуста) → JWT |
| POST | `/api/v1/auth/login` | Вход → JSON `access_token` / `token_type` |
| POST | `/api/v1/auth/logout` | Заглушка; токен сбрасывается на клиенте |
| GET | `/api/v1/auth/me` | Текущий админ по заголовку `Authorization: Bearer …` |
| GET | `/api/v1/admin/settings/all` | Все записи справочника (**JWT**) |
| POST | `/api/v1/admin/settings` | Добавить услугу/диапазон бюджета (**JWT**) |
| PATCH | `/api/v1/admin/settings/{id}` | Обновить (**JWT**) |
| DELETE | `/api/v1/admin/settings/{id}` | Удалить (**JWT**) |

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

### Доступ к PostgreSQL

Контейнер **postgres** не публикует `5432` на хост. Удобный вариант: `docker compose exec -it postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'`. Для клиента на хосте можно временно добавить `ports: ["5432:5432"]` в `docker-compose.yml` (только в доверенной среде).

### Локальная разработка frontend (`vite`)

При запущенном стеке Compose запросы к **`/api`** проксируются на `http://127.0.0.1:8080` (Nginx → backend).

```bash
cd frontend
npm install
npm run dev
```

Открыть **`http://127.0.0.1:5173/`** (клиент) и **`http://127.0.0.1:5173/admin/`** (админ).

### Локальная разработка backend (без пересборки образа)

Нужен свой **DATABASE_URL** в `.env` (async, например `postgresql+asyncpg://…`) и доступ к Postgres по TCP. Задайте **`SECRET_KEY`** (≥ 32 символов) для подписи JWT.

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
| `NGINX_HTTP_PORT` | нет | Порт хоста → HTTP (по умолчанию `8080`) |
| `DATABASE_URL` | нет в Compose | Задаётся в `docker-compose` для `backend`; для локального uvicorn — в `.env` |
| `SECRET_KEY` | да (в Compose) | Случайная строка ≥ 32 символов; подпись JWT |
| `DOCS_ENABLED` | нет | `true` / `false` — OpenAPI UI и схема (по умолчанию `false`) |

`DATABASE_URL` в Docker: `postgresql+asyncpg://…` (см. `docker-compose.yml`).

Локально при `uvicorn` задайте тот же **`SECRET_KEY`**, что в Docker, иначе токены не будут валидны между средами.

## Разработка и тесты

```bash
docker compose config
docker compose logs -f backend
python3 -m compileall -q backend/app
```

При расширении проекта — `pytest`, `ruff`/`mypy` по необходимости.
