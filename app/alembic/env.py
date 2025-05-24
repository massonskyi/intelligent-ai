from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
# --- НАЧАЛО ИЗМЕНЕНИЙ ДЛЯ SQLMODEL И ASYNC ---
import asyncio
import os
import sys

# Добавляем путь к проекту, чтобы Alembic мог найти модули приложения
# Путь ../.. потому что env.py находится в app/alembic/
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..")))

from models.orm import SQLModel  # Импортируем SQLModel из вашего orm.py
from db.database import DATABASE_URL # Используем URL из вашего database.py

# Устанавливаем target_metadata на метаданные вашей SQLModel
target_metadata = SQLModel.metadata
# --- КОНЕЦ ИЗМЕНЕНИЙ ДЛЯ SQLMODEL И ASYNC ---

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None # Заменено выше

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # url = config.get_main_option("sqlalchemy.url") # Используем DATABASE_URL
    context.configure(
        url=DATABASE_URL, # Используем импортированный DATABASE_URL
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True, # Для лучшей совместимости с SQLModel
    )

    with context.begin_transaction():
        context.run_migrations()

# Вспомогательная синхронная функция для run_sync
def do_run_migrations(connection):
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        compare_type=True, # Для лучшей совместимости с SQLModel
        # Если используете transactional_ddl=False в PostgreSQL, можно добавить:
        # transactional_ddl=False 
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Убедимся, что alembic.ini использует правильный URL, если он там задан,
    # иначе используем наш DATABASE_URL.
    alembic_config_url = config.get_main_option("sqlalchemy.url")
    current_db_url = alembic_config_url if alembic_config_url else DATABASE_URL
    
    # Если URL в alembic.ini не совпадает с DATABASE_URL и DATABASE_URL не дефолтный sqlite,
    # возможно, стоит выдать предупреждение или обновить config.
    # Для простоты, просто используем DATABASE_URL, если alembic_config_url пуст.
    if not alembic_config_url:
        config.set_main_option("sqlalchemy.url", DATABASE_URL) # Обновляем конфиг Alembic

    from sqlalchemy.ext.asyncio import create_async_engine

    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"), # Берем URL из конфига Alembic
        poolclass=pool.NullPool,
        future=True # future=True рекомендуется для SQLAlchemy 2.0+
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
