"""AbstractManager: create/read/update/delete for every manager (SDD contracts 2-5).

Subclasses set TABLE, PK, COLUMNS and REQUIRED (and UPDATABLE when some columns
may be set on create but never changed), and implement can_perform().
They do not rewrite the CRUD methods.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from Db import Db


class AbstractManager(ABC):
    TABLE: str = ""        # table name, e.g. "buckets"
    PK: str = "id"         # primary key column, e.g. "bucket_id"
    COLUMNS: tuple = ()    # columns callers may set on create
    UPDATABLE = None       # columns callers may change later (defaults to COLUMNS)
    REQUIRED: tuple = ()   # columns that must be present on create

    def __init__(self, db: Db):
        if not self.TABLE or not self.COLUMNS:
            raise TypeError(f"{type(self).__name__} must define TABLE and COLUMNS")
        self.db = db

    @abstractmethod
    def can_perform(self, action: str, actor_id: int,
                    record_id: int | None = None, data: dict | None = None) -> bool:
        """True if actor_id may do action ("create", "read", "update", "delete").
        record_id is None for create. data is the new record (create) or the
        requested changes (update)."""

    # ---- helpers -------------------------------------------------------
    @staticmethod
    def _check_columns(data: dict, allowed: tuple) -> None:
        bad = set(data) - set(allowed)
        if bad:
            raise ValueError(f"unknown or protected fields: {sorted(bad)}")

    def _require(self, action: str, actor_id: int,
                 record_id: int | None = None, data: dict | None = None) -> None:
        if not self.can_perform(action, actor_id, record_id, data):
            raise PermissionError(f"user {actor_id} may not {action} {self.TABLE}")

    def _fetch(self, record_id: int) -> dict | None:
        rows = self.db.execute(
            f"SELECT * FROM {self.TABLE} WHERE {self.PK} = ?", (record_id,))
        return rows[0] if rows else None

    # ---- contract 2: Create --------------------------------------------
    def create(self, data: dict, actor_id: int) -> int:
        """Store a new record and return its ID.

        @requires data is a non-empty dict using only allowed columns
        @requires data includes every REQUIRED column
        @requires actor_id may create this record type
        @ensures exactly one new row exists and its ID is returned
        @ensures nothing is written if validation or permission fails
        @return int
        """
        if not isinstance(data, dict) or not data:
            raise ValueError("data must be a non-empty dict")
        self._check_columns(data, self.COLUMNS)
        missing = [c for c in self.REQUIRED if c not in data]
        if missing:
            raise ValueError(f"missing required fields: {missing}")
        self._require("create", actor_id, data=data)

        cols = list(data)
        marks = ", ".join("?" for _ in cols)
        self.db.execute(
            f"INSERT INTO {self.TABLE} ({', '.join(cols)}) VALUES ({marks})",
            tuple(data[c] for c in cols))
        return self.db.last_row_id

    # ---- contract 3: Read ----------------------------------------------
    def read(self, record_id: int, actor_id: int) -> dict:
        """Retrieve a record by ID.

        @requires the record exists
        @requires actor_id may read it
        @ensures the record is returned and the database is unchanged
        @return dict
        """
        record = self._fetch(record_id)
        if record is None:
            raise LookupError(f"{self.TABLE} {record_id} not found")
        self._require("read", actor_id, record_id)
        return record

    # ---- contract 4: Update --------------------------------------------
    def update(self, record_id: int, changes: dict, actor_id: int) -> bool:
        """Change allowed fields on a record.

        @requires the record exists
        @requires changes is a non-empty dict using only updatable columns
        @requires actor_id may edit it
        @ensures the listed fields are saved and all other fields are unchanged
        @return bool (True on success)
        """
        if self._fetch(record_id) is None:
            raise LookupError(f"{self.TABLE} {record_id} not found")
        if not isinstance(changes, dict) or not changes:
            raise ValueError("changes must be a non-empty dict")
        self._check_columns(changes, self.UPDATABLE or self.COLUMNS)
        self._require("update", actor_id, record_id, changes)

        sets = ", ".join(f"{c} = ?" for c in changes)
        self.db.execute(
            f"UPDATE {self.TABLE} SET {sets} WHERE {self.PK} = ?",
            tuple(changes.values()) + (record_id,))
        return self.db.rowcount == 1

    # ---- contract 5: Delete --------------------------------------------
    def delete(self, record_id: int, actor_id: int) -> bool:
        """Remove a record.

        @requires the record exists
        @requires actor_id may delete it
        @ensures the record no longer exists
        @return bool (True on success)
        """
        if self._fetch(record_id) is None:
            raise LookupError(f"{self.TABLE} {record_id} not found")
        self._require("delete", actor_id, record_id)
        self.db.execute(
            f"DELETE FROM {self.TABLE} WHERE {self.PK} = ?", (record_id,))
        return self.db.rowcount == 1