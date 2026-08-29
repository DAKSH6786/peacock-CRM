from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool, text

# Ensure Peacock One's backend/engines/plugins packages are importable
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [
    str(ROOT),
    str(ROOT / "backend"),
    str(ROOT / "backend" / "packages"),
    str(ROOT / "backend" / "services"),
    str(ROOT / "engines" / "seo"),
    str(ROOT / "engines" / "aeo"),
    str(ROOT / "engines" / "geo"),
    str(ROOT / "engines" / "crawler"),
    str(ROOT / "engines" / "competitor-intelligence"),
    str(ROOT / "engines" / "llm-intelligence"),
    str(ROOT / "plugins"),
]

from api.config import get_settings  # noqa: E402
from db_models import Base  # noqa: E402
import db_models  # noqa: F401,E402 — register models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.commit()
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
