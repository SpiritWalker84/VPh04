# VPh04: Nginx + PostgreSQL + pgAdmin (инфра под backend)

## Краткое описание

**Что делает.** Контейнерная **инфраструктура** под будущее веб-приложение (форма лидов, API, БД): **Nginx** — единая точка входа по **HTTP** на порту хоста; **PostgreSQL** — только внутри сети Docker (на хост не публикуется); **pgAdmin** — администрирование БД из браузера. Префикс **`/api/`** в Nginx зарезервирован под проксирование на контейнер **`backend`** (сервис в Compose пока **закомментирован**).

**Как запускать.** Из корня: `cp .env.example .env` (пароли, при необходимости порты), затем `docker compose up -d`. Проверка: `docker compose ps` (без циклических перезапусков). Логи: `docker compose logs -f nginx` / `postgres` / `pgadmin`. Остановка: `docker compose down`.

**HTTP и TLS.** По умолчанию трафик к Nginx и pgAdmin — **HTTP**. Если нужен **HTTPS**, настройте TLS отдельно (внешний прокси, сертификаты в Nginx и т.п.).

**Ограничения:** в репозитории **нет** кода backend/frontend и **нет** собранных образов приложения до появления `backend/Dockerfile`. Данные PostgreSQL живут в **Docker volume** `postgres_data`, не в путях git.

Структура и оформление согласованы с [Guide](https://github.com/SpiritWalker84/Guide) (`docs/conventions/`).

## Стек

**Docker** / **Docker Compose v2** (команда `docker compose`, не устаревший бинарь `docker-compose`), **Nginx** 1.27 (Alpine), **PostgreSQL** 16 (Alpine), **pgAdmin 4** (`dpage/pgadmin4`).

## Структура

| Путь | Назначение |
|------|------------|
| `docker-compose.yml` | Сервисы `postgres`, `pgadmin`, `nginx`; задел под `backend` (закомментирован). |
| `docker/nginx/conf.d/default.conf` | Виртуальный хост: статика, прокси `/api/` на `backend:8000`. |
| `docker/nginx/html/` | Статическая заглушка для проверки Nginx. |
| `.env.example` | Шаблон переменных окружения (без секретов). |
| `.gitignore` | Игнор `.env`. |

После появления backend ожидается каталог `backend/` с `Dockerfile` и кодом приложения; первый подъём с пересборкой: `docker compose up -d --build`.

## Запуск

### Docker Compose (основной способ)

```bash
cp .env.example .env
# POSTGRES_*; PGADMIN_DEFAULT_*; при необходимости NGINX_HTTP_PORT, PGADMIN_PORT

docker compose up -d
docker compose ps
```

Проверка в браузере (порты по умолчанию из `.env.example`):

- Nginx: `http://localhost:8080/`
- Префикс API: `http://localhost:8080/api/` — пока **backend** не поднят, ожидаемо **502** от прокси.
- pgAdmin: `http://localhost:5050/`

### pgAdmin: сервер PostgreSQL

В интерфейсе **Register → Server** поле **Name** (General) — любое имя в дереве, например `VPh04 Postgres`. Подключение (**Connection**):

| Поле | Значение |
|------|----------|
| Host name/address | `postgres` (имя сервиса в Compose, не `localhost` с хоста) |
| Port | `5432` |
| Maintenance database | `POSTGRES_DB` из `.env` |
| Username | `POSTGRES_USER` из `.env` |
| Password | `POSTGRES_PASSWORD` из `.env` |

**Важно:** у pgAdmin логин — email из `PGADMIN_DEFAULT_EMAIL`; домены вроде `.local` новые версии могут отклонять — в `.env.example` задан приемлемый вид (`admin@example.com`).

### Проверка Compose без подъёма контейнеров

```bash
docker compose config
```

## Конфигурация

См. **`.env.example`**. Секреты в git не коммитить.

| Переменная | Обязательность | Описание |
|------------|----------------|----------|
| `POSTGRES_USER` | да | Пользователь БД |
| `POSTGRES_PASSWORD` | да | Пароль БД |
| `POSTGRES_DB` | да | Имя базы |
| `PGADMIN_DEFAULT_EMAIL` | да | Логин в веб-интерфейс pgAdmin |
| `PGADMIN_DEFAULT_PASSWORD` | да | Пароль pgAdmin |
| `NGINX_HTTP_PORT` | нет | Порт хоста → HTTP Nginx (по умолчанию `8080`) |
| `PGADMIN_PORT` | нет | Порт хоста → pgAdmin (по умолчанию `5050`) |

PostgreSQL **не** проброшен на хост; доступ извне контейнеров — через приложение (после появления backend) или через pgAdmin на отдельном порту.

## Разработка и тесты

```bash
docker compose config
```

Отдельные тесты и линтеры приложения появятся с кодом backend/frontend. При добавлении — типично `pytest`, линтеры стека.
