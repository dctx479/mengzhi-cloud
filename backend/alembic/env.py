"""Alembic migration environment configuration

版本: 1.0
更新日期: 2026-01-17

此文件处理SQLAlchemy配置，并在迁移时调用
自动检测模型变更并生成迁移脚本
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
from pathlib import Path

# 添加app目录到Python路径
from app.models.base import Base
from app.models.user import User
from app.models.enterprise import Enterprise
from app.models.product import Product
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.sla import SLAAgreement, SLAMetric, SLAViolation, PerformanceLog
from app.core.config import settings

# this is the Alembic Config object, which provides
# the values of the [alembic] section of the alembic.ini
# file as Python dictionary for use in process_migrate_env.py
config = context.config

# Interpret the config file for Python logging.
# This code creates the logging configuration from the alembic.ini file,
# relating to the defaults present when
# the .exe file was first invoked. Custom logging
# configuration can be supplied instead if desired.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the [alembic] section
# and/or those to environ variables, can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    without an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
