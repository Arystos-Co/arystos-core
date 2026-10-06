"""SQLite connection management and database migrations."""

import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).resolve().parent.parent / "arystos.db"
MIGRATIONS_PATH = Path(__file__).resolve().parent / "migrations"


def get_connection() -> sqlite3.Connection:
    """Open and return a SQLite connection configured for named-row access."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@asynccontextmanager
async def get_async_connection() -> AsyncIterator[aiosqlite.Connection]:
    """Yield an async SQLite connection configured for named-row access.

    Returns:
        An async iterator yielding an open connection with named-row access.

    Raises:
        aiosqlite.Error: If the database connection cannot be opened.
    """
    connection = await aiosqlite.connect(DB_PATH)
    connection.row_factory = aiosqlite.Row
    try:
        yield connection
    finally:
        await connection.close()


def init_db() -> None:
    """Create the migration table and apply each pending SQL migration."""
    connection = get_connection()
    try:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(filename TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        connection.commit()

        migration_files = sorted(MIGRATIONS_PATH.glob("*.sql"))
        for migration_file in migration_files:
            applied = connection.execute(
                "SELECT 1 FROM schema_migrations WHERE filename = ?",
                (migration_file.name,),
            ).fetchone()
            if applied is not None:
                continue

            migration_sql_lines = migration_file.read_text(encoding="utf-8").splitlines(
                keepends=True
            )
            statement_lines: list[str] = []
            connection.execute("BEGIN")
            try:
                for line in migration_sql_lines:
                    statement_lines.append(line)
                    statement = "".join(statement_lines)
                    if sqlite3.complete_statement(statement):
                        connection.execute(statement)
                        statement_lines.clear()

                if any(line.strip() for line in statement_lines):
                    raise sqlite3.OperationalError(
                        f"Incomplete SQL statement in migration {migration_file.name}"
                    )

                connection.execute(
                    "INSERT INTO schema_migrations (filename, applied_at) VALUES (?, ?)",
                    (
                        migration_file.name,
                        datetime.now(UTC).isoformat(),
                    ),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
    finally:
        connection.close()


if __name__ == "__main__":
    init_db()
    print("Database initialised.")
