import os
import sqlite3
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "kenyabiz.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


# ============================================================
# DATABASE PATH
# ============================================================

def get_database_path():
    """
    Return the database path used by the application.

    By default, KenyaBiz uses the normal development database.

    Tests can override this using the KENYABIZ_DATABASE
    environment variable.
    """

    configured_path = os.getenv("KENYABIZ_DATABASE")

    if configured_path:
        return Path(configured_path)

    return DEFAULT_DATABASE_PATH


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create and return a connection to the KenyaBiz SQLite database.
    """

    database_path = get_database_path()

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(database_path)

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():
    """
    Create database tables using schema.sql.
    """

    connection = get_connection()

    try:

        with open(
            SCHEMA_PATH,
            "r",
            encoding="utf-8",
        ) as file:

            schema = file.read()

        connection.executescript(schema)

        connection.commit()

    finally:
        connection.close()


# ============================================================
# TEST DATABASE
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("KENYABIZ AI")
    print("Database Initialization")
    print("=" * 60)

    initialize_database()

    print()
    print("Database used:")
    print(get_database_path())

    print()
    print("Database initialization completed successfully.")