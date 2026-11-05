"""Creates the local SQLite database the first time it is run.

Usage (from the repo root):
    python backend/database/init_db.py            # create the DB if it does not exist
    python backend/database/init_db.py --reset    # delete and rebuild it (wipes all data)

Uses only the Python standard library, so there is nothing to install.
"""
import argparse
import sqlite3
from pathlib import Path

baseDir = Path(__file__).resolve().parent
schemaPath = baseDir / "schema.sql"
dbPath = baseDir / "bucketlist.db"   # git-ignored; each developer has their own copy


def get_connection():
    """Open a connection with foreign keys enforced. Import this from the backend."""
    connection = sqlite3.connect(dbPath)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


def init_db(isReset=False):
    if isReset and dbPath.exists():
        dbPath.unlink()
        print(f"Deleted {dbPath.name}")

    isNew = not dbPath.exists()
    connection = get_connection()
    try:
        connection.executescript(schemaPath.read_text())
        connection.commit()
    finally:
        connection.close()

    print(("Created" if isNew else "Verified") + f" database at {dbPath}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up the Bucket List database.")
    parser.add_argument("--reset", action="store_true", help="delete and rebuild the database")
    args = parser.parse_args()
    init_db(args.reset)