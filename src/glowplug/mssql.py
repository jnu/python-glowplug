from sqlalchemy.ext.asyncio import create_async_engine
from .base import DbDriver


class MsSqlDriver(DbDriver):
    """Microsoft SQL Server database driver."""

    path: str

    def __init__(self, path: str, **kwargs):
        """Initialize the driver.

        Args:
            path (str): The path to connect to the database.
        """
        super().__init__(**kwargs)
        self.path = path

    async def exists(self) -> bool:
        """Check if the database exists."""
        # Get a database-less path and the db name
        path, database = self._split_path()
        # Connect to the database-less path
        engine = create_async_engine(f"mssql+aioodbc://{path}")
        async with engine.connect() as conn:
            # Check if the database exists
            result = await conn.execute(
                f"SELECT name FROM sys.databases WHERE name = '{database}'"
            )
            row = await result.fetchone()
            return row is not None

    async def create(self) -> None:
        """Create the database."""
        # Get a database-less path and the db name
        path, database = self._split_path()
        # Connect to the database-less path
        engine = create_async_engine(f"mssql+aioodbc://{path}")
        async with engine.connect() as conn:
            # Create the database
            await conn.execute(f"CREATE DATABASE {database}")

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
        # Re-join the query to the beginning of the path
        path = f"{head}/?{query}"
        return path, database
