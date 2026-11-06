"""Db: the only class that talks to the SQLite database (SDD contract 1)."""
from __future__ import annotations
import sqlite3


class Db:
    def __init__(self, path: str = "bucketlist.db", connect=None):
        """connect: optional function returning a ready sqlite3 connection,
        e.g. get_connection from init_db.py. If omitted, opens `path`."""
        self.path = path
        self._connect = connect or self._default_connect
        self.last_row_id = None  # id of the last inserted row
        self.rowcount = 0        # rows changed by the last statement

    def _default_connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def execute(self, sql: str, params: tuple = ()) -> list[dict]:
        """Run a parameterized query and return its rows.

        @requires sql is a non-empty string
        @requires params match the placeholders (?) in sql
        @ensures the query runs in a transaction
        @ensures changes are committed on success, rolled back on error
        @return list[dict] (empty for INSERT/UPDATE/DELETE)
        """
        if not sql or not sql.strip():
            raise ValueError("sql must be a non-empty string")

        conn = self._connect()
        try:
            cur = conn.execute(sql, params)
            rows = [dict(r) for r in cur.fetchall()]
            self.last_row_id = cur.lastrowid
            self.rowcount = cur.rowcount
            conn.commit()
            return rows
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def run_script(self, script: str) -> None:
        """Run a multi-statement SQL script, e.g. the schema file."""
        conn = self._connect()
        try:
            conn.executescript(script)
            conn.commit()
        finally:
            conn.close()