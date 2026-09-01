import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
import asyncio
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import create_async_engine

# Ensure the root project directory is in the sys.path so absolute imports work smoothly
root_dir = str(Path(__file__).resolve().parents[3])
if root_dir not in sys.path:
    sys.path.append(root_dir)

# --- 1. IMPORT YOUR METADATA & MODELS HERE ---
# Adjust to 'from app.db.init_db import Base' if Base is defined there instead
from app.db.database import Base
from app.models.module import UserLog

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.

# pylint: disable=no-member
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- 2. SET TARGET METADATA FOR AUTOGENERATE ---
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "pyformat"},
    )


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection with
    the context.
    """
    # 1. Read configuration sections
    configuration = config.get_section(config.config_ini_section, {})

    # 2. Extract database URL from configuration
    url = configuration.get("sqlalchemy.url") or config.get_main_option(
        "sqlalchemy.url"
    )

    # 3. Explicitly create an Async Engine
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )

    # 4. Helper function to process migrations inside the sync context manager
    def do_run_migrations(connection):
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    # 5. Core async wrapper to connect and run
    async def run_async_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()

    # 6. Trigger the async cycle
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
