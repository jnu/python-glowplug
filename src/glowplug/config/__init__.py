from functools import cached_property
from typing import Literal

from pydantic import BaseModel

from ..driver.mssql import MsSqlDriver
from ..driver.pg import PostgresDriver
from ..driver.sqlite import SqliteDriver


class SqliteSettings(BaseModel):
    """Settings for connecting to SQLite."""

    engine: Literal["sqlite"]
    path: str = ":memory:"

    @cached_property
    def driver(self) -> SqliteDriver:
        return SqliteDriver(self.path)


class PostgresSettings(BaseModel):
    """Settings for connecting to Postgres."""

    engine: Literal["postgres"]
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str
    database: str
    maintenance_db: str | None = None

    @cached_property
    def driver(self) -> PostgresDriver:
        url = f"{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return PostgresDriver(url, maintenance_db=self.maintenance_db)


class MsSqlSettings(BaseModel):
    """Settings for connecting to Microsoft SQL Server."""

    engine: Literal["mssql"]
    odbc_driver: Literal["ODBC Driver 17 for SQL Server"] = (
        "ODBC Driver 17 for SQL Server"
    )
    host: str = "127.0.0.1"
    port: int = 1433
    user: str = "sa"
    password: str
    database: str
    maintenance_db: str = "master"

    @cached_property
    def driver(self):
        odbc_driver = self.odbc_driver.replace(" ", "+")
        path = (
            f"{self.user}:{self.password}@{self.host}:{self.port}"
            f"/{self.database}?driver={odbc_driver}"
        )
        return MsSqlDriver(path, maintenance_db=self.maintenance_db)
