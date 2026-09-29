import sqlite3
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "data" / "kenyabiz.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create and return a connection to the KenyaBiz SQLite database.
    """

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

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
        with open(SCHEMA_PATH, "r", encoding="utf-8") as file:
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
    print(f"Database created at:")
    print(DATABASE_PATH)

    print()
    print("Database initialization completed successfully.")