Glowplug
===

A consistent interface for maintenance operations on database engines not covered by SQLAlchemy.

Chooses opinionated drivers with both async + sync support.

## Supported operations

 - `exists` - Check if database exists
 - `create` - Create a new database
 - `init` - Create all tables in the given database, optionally dropping first

## Supported databases

 - SQLite (`aiosqlite`)
 - Postgres (`asyncpg`)
 - MS Sql (`pyodbc` and `aioodbc`)
