from abc import ABC, abstractmethod
from functools import cached_property
from typing import Any

import alembic
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class AlembicCommandProxy:
    """Proxy for running alembic commands with a given config."""

    def __init__(self, config: alembic.config.Config) -> None:
        self.config = config

    def __getattribute__(self, name: str) -> Any:
        cmd = getattr(alembic.command, name)
        if callable(cmd):
            return lambda *args, **kwargs: cmd(self.config, *args, **kwargs)
        return super().__getattribute__(name)


class DbDriver(ABC):
    def __init__(
        self, debug: bool = False, alembic_config: str = "alembic.ini"
    ) -> None:
        self.debug = debug
        self.alembic_config = alembic_config

    @abstractmethod
    async def exists(self) -> bool:
        """Check if the database exists."""
        ...

    @abstractmethod
    async def create(self) -> None:
        """Create the database."""
        ...

    @property
    @abstractmethod
    def async_uri(self) -> str:
        """The async uri."""
        ...

    @property
    @abstractmethod
    def sync_uri(self) -> str:
        """The sync uri."""
        ...

    async def init(self, base: DeclarativeBase, drop_first: bool = False) -> None:
        """Initialize the database."""
        engine = self.get_async_engine()
        async with engine.begin() as conn:
            if drop_first:
                await conn.run_sync(base.metadata.drop_all)
            await conn.run_sync(base.metadata.create_all)
        await engine.dispose()

    def get_async_engine(self) -> AsyncEngine:
        """Get an async engine."""
        return create_async_engine(self.async_uri, echo=self.debug)

    def get_sync_engine(self) -> Engine:
        """Get a sync engine."""
        return create_engine(self.sync_uri, echo=self.debug)

    @cached_property
    def async_session(self) -> AsyncSession:
        """Get an async session."""
        return async_sessionmaker(self.get_async_engine(), expire_on_commit=False)

    @cached_property
    def sync_session(self) -> Session:
        """Get a sync session."""
        return sessionmaker(self.get_sync_engine(), expire_on_commit=False)

    @cached_property
    def alembic(self) -> AlembicCommandProxy:
        """Get an alembic command proxy."""
        # Use the Alembic config from `alembic.ini` but override the URL for the db
        al_cfg = alembic.config.Config(self.alembic_config)
        al_cfg.set_main_option("sqlalchemy.url", self.sync_uri)
        return AlembicCommandProxy(al_cfg)
