from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from .base import DbDriver


class MsSqlDriver(DbDriver):
    """Microsoft SQL Server database driver."""

    path: str

    maintenance_db: str

    def __init__(self, path: str, maintenance_db: str = "master", **kwargs):
        """Initialize the driver.

        Args:
            path (str): The path to connect to the database.
            maintenance_db (str, optional): The database to connect to for maintenance. Defaults to "master".
        """
        super().__init__(**kwargs)
        self.path = path
        self.maintenance_db = maintenance_db

    async def exists(self) -> bool:
        """Check if the database exists."""
        # Get a database-less path and the db name
        path, database = self._split_path()
        # Connect to the database-less path
        engine = create_async_engine(f"mssql+aioodbc://{path}")
        try:
            async with engine.connect() as conn:
                # Check if the database exists
                result = await conn.execute(
                    text("SELECT name FROM sys.databases WHERE name = :db"),
                    {"db": database},
                )
                row = result.fetchone()
                return row is not None
        finally:
            await engine.dispose()

    async def create(self) -> None:
        """Create the database."""
        # Get a database-less path and the db name
        path, database = self._split_path()
        # Connect to the database-less path
        engine = create_async_engine(f"mssql+aioodbc://{path}")
        # Need to run this with autocommit=True to avoid a transaction error
        # See: https://stackoverflow.com/a/42008664
        try:
            async with engine.connect() as conn:
                rc = await conn.get_raw_connection()
                rc.driver_connection.autocommit = True
                await conn.execute(text(f"CREATE DATABASE {database}"))
        finally:
            await engine.dispose()

    @property
    def async_uri(self) -> str:
        """Connect with aioodbc."""
        return f"mssql+aioodbc://{self.path}"

    @property
    def sync_uri(self) -> str:
        """Connect with pyodbc."""
        return f"mssql+pyodbc://{self.path}"

    def _split_path(self) -> tuple[str, str]:
        """Extract the database name from the rest of the path."""
        # Split the path into everything before the / and after
        head, tail = self.path.split("/", 1)
        # Extract the database name from the tail
        database, query = tail.split("?", 1)
        # Re-join the query to the beginning of the path, with the
        # name of the maintenance database.
        path = f"{head}/{self.maintenance_db}?{query}"
        return path, database
