from abc import ABC, abstractmethod
from functools import cached_property, cache
from typing import Any, List

import alembic
import alembic.command
import alembic.config
from sqlalchemy import Engine, create_engine, inspect
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
        cmd = getattr(alembic.command, name, None)
        if callable(cmd):
            cfg = super().__getattribute__("config")
            return lambda *args, **kwargs: cmd(cfg, *args, **kwargs)
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

    def list_tables(self) -> List[str]:
        """List tables in the database."""
        # TODO: sqlalchemy doesn't have an async `inspect` API.
        # Presumably this won't be run any context where that matters much,
        # but ideally we'd have a way to do this async.
        engine = self.get_sync_engine()
        try:
            inspector = inspect(engine)
            return inspector.get_table_names()
        finally:
            engine.dispose()

    async def is_blank_slate(self) -> bool:
        """Helper to check if the database is missing or has no tables.

        Returns:
            bool: True if the database is a blank slate, False otherwise.
        """
        if not await self.exists():
            return True

        if not self.list_tables():
            return True

        return False

    async def init(self, base: DeclarativeBase, drop_first: bool = False) -> None:
        """Initialize the database."""
        engine = self.get_async_engine()
        async with engine.begin() as conn:
            if drop_first:
                await conn.run_sync(base.metadata.drop_all)
            await conn.run_sync(base.metadata.create_all)
        await engine.dispose()

    def get_async_engine(self, **kwargs) -> AsyncEngine:
        """Get an async engine."""
        return create_async_engine(self.async_uri, echo=self.debug, **kwargs)

    def get_sync_engine(self, **kwargs) -> Engine:
        """Get a sync engine."""
        return create_engine(self.sync_uri, echo=self.debug, **kwargs)

    @cache
    def async_session_with_args(self, **kwargs) -> AsyncSession:
        """Get an async session with arguments."""
        return async_sessionmaker(
            self.get_async_engine(**kwargs), expire_on_commit=False
        )

    @cached_property
    def async_session(self) -> AsyncSession:
        """Get an async session."""
        return self.async_session_with_args()

    @cache
    def sync_session_with_args(self, **kwargs) -> Session:
        """Get a sync session with arguments."""
        return sessionmaker(self.get_sync_engine(**kwargs), expire_on_commit=False)

    @cached_property
    def sync_session(self, **kwargs) -> Session:
        """Get a sync session."""
        return self.sync_session_with_args()

    @cached_property
    def alembic(self) -> AlembicCommandProxy:
        """Get an alembic command proxy."""
        # Use the Alembic config from `alembic.ini` but override the URL for the db
        al_cfg = alembic.config.Config(self.alembic_config)
        al_cfg.set_main_option("sqlalchemy.url", self.sync_uri)
        return AlembicCommandProxy(al_cfg)
