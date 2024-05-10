Glowplug
===

A consistent interface for maintenance operations on database engines not covered by SQLAlchemy.

Chooses opinionated drivers with both async + sync support, as well as support for Alembic.

## Supported operations

 - `exists` - Check if database exists
 - `create` - Create a new database
 - `init` - Create all tables in the given database, optionally dropping first
 - `alembic` - Run any of the alembic commands on the given database

## Supported databases

 - SQLite (`aiosqlite`)
 - Postgres (`asyncpg`)
 - MS Sql (`pyodbc` and `aioodbc`)
