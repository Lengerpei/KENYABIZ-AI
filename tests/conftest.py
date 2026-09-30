import os
import tempfile
from pathlib import Path

import pytest

from src.database.database import initialize_database
from src.tools.product_tool import load_products_from_csv


# ============================================================
# TEST DATABASE FIXTURE
# ============================================================

@pytest.fixture(scope="session", autouse=True)
def test_database():
    """
    Create an isolated SQLite database for the entire pytest session.

    The application will use this database instead of the normal
    development database.

    The database is automatically removed after the test session.
    """

    # --------------------------------------------------------
    # Create temporary database
    # --------------------------------------------------------

    temporary_directory = tempfile.TemporaryDirectory(
        prefix="kenyabiz_test_"
    )

    test_database_path = (
        Path(temporary_directory.name) / "kenyabiz_test.db"
    )

    # --------------------------------------------------------
    # Tell the application to use the test database
    # --------------------------------------------------------

    os.environ["KENYABIZ_DATABASE"] = str(test_database_path)

    try:

        # ----------------------------------------------------
        # Create database tables
        # ----------------------------------------------------

        initialize_database()

        # ----------------------------------------------------
        # Load product catalogue
        # ----------------------------------------------------

        load_products_from_csv()

        # ----------------------------------------------------
        # Run tests
        # ----------------------------------------------------

        yield test_database_path

    finally:

        # ----------------------------------------------------
        # Remove environment variable
        # ----------------------------------------------------

        os.environ.pop("KENYABIZ_DATABASE", None)

        # ----------------------------------------------------
        # Delete temporary database
        # ----------------------------------------------------

        temporary_directory.cleanup()