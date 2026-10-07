from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from alembic import context
from app.models.password_reset_token import PasswordResetToken
from app.config.settings import settings
from app.database.base import Base
from app.models import *

# Alembic Config object
config = context.config

# Set the database URL from application settings
sync_database_url = settings.DATABASE_URL.replace(
    "postgresql+asyncpg",
    "postgresql+psycopg",
)

config.set_main_option(
    "sqlalchemy.url",
    sync_database_url,
)

# Configure Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()