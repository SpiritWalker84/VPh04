-- Ручное создание таблицы admins (эквивалент миграции Alembic 20260507_0002).
-- Выполнять в БД только если миграции не прогонялись; иначе достаточно `alembic upgrade head`.

CREATE TABLE IF NOT EXISTS admins (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(128) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_admins_username ON admins (username);
