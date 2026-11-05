"""Task: an assignment inside a category (SDD contracts 11, 12, 13)."""
from __future__ import annotations

from datetime import datetime

from abstract_manager import AbstractManager


class Task(AbstractManager):
    TABLE = "tasks"
    PK = "task_id"
    # notes, subtasks and completion change only through their own contracts
    COLUMNS = ("category_id", "user_id", "task_name", "task_description",
               "due_date", "urgency", "is_on_hold")
    UPDATABLE = ("user_id", "task_name", "task_description",
                 "due_date", "urgency", "is_on_hold")
    REQUIRED = ("category_id", "task_name")

    def __init__(self, db, buckets):
        super().__init__(db)
        self.buckets = buckets  # Bucket manager, for permission checks

    def bucket_of(self, task_id: int):
        rows = self.db.execute(
            "SELECT c.bucket_id FROM tasks t "
            "JOIN categories c ON c.category_id = t.category_id WHERE t.task_id = ?",
            (task_id,))
        return rows[0]["bucket_id"] if rows else None

    def can_perform(self, action, actor_id, record_id=None, data=None):
        if action == "create":
            rows = self.db.execute(
                "SELECT bucket_id FROM categories WHERE category_id = ?",
                ((data or {}).get("category_id"),))
            bucket_id = rows[0]["bucket_id"] if rows else None
            needed = "create_task"
        else:
            bucket_id = self.bucket_of(record_id)
            needed = {"read": "view", "update": "edit", "delete": "delete"}[action]
        if bucket_id is None:
            return False
        return self.buckets.has_permission(bucket_id, actor_id, needed)

    def _existing(self, task_id: int) -> dict:
        task = self._fetch(task_id)
        if task is None:
            raise LookupError(f"tasks {task_id} not found")
        return task

    # ---- contract 11: Notes --------------------------------------------
    def add_note(self, task_id: int, text: str, actor_id: int) -> int:
        """Add a note to a task. Notes live in one text column, one line each:
        "[YYYY-MM-DD HH:MM] username: text".

        @requires task exists
        @requires actor is a member of the task's bucket
        @requires text nonempty
        @ensures note saved with author and time
        @ensures other task fields unchanged
        @return int (the note's position, starting at 1)
        """
        task = self._existing(task_id)
        if not self.buckets.has_permission(self.bucket_of(task_id), actor_id, "add_note"):
            raise PermissionError(f"user {actor_id} may not add notes here")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")

        author = self.db.execute(
            "SELECT username FROM users WHERE user_id = ?", (actor_id,))[0]["username"]
        line = f"[{datetime.now():%Y-%m-%d %H:%M}] {author}: {' '.join(text.split())}"
        existing = task["notes"] or ""
        self.db.execute("UPDATE tasks SET notes = ? WHERE task_id = ?",
                        ((existing + "\n" if existing else "") + line, task_id))
        return len(existing.splitlines()) + 1

    # ---- contract 12: Subtasks -----------------------------------------
    def add_subtask(self, task_id: int, title: str, actor_id: int) -> int:
        """Add a subtask (a task row pointing at its parent).

        @requires task exists and is not itself a subtask
        @requires actor is a member of the task's bucket
        @requires title nonempty
        @ensures subtask saved under the task, in the same category
        @ensures parent task unchanged
        @return int
        """
        parent = self._existing(task_id)
        if parent["parent_task_id"] is not None:
            raise ValueError("subtasks cannot have subtasks")
        if not self.buckets.has_permission(self.bucket_of(task_id), actor_id, "add_subtask"):
            raise PermissionError(f"user {actor_id} may not add subtasks here")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must be a non-empty string")

        self.db.execute(
            "INSERT INTO tasks (category_id, parent_task_id, task_name) VALUES (?, ?, ?)",
            (parent["category_id"], task_id, title.strip()))
        return self.db.last_row_id

    # ---- contract 13: Completion ---------------------------------------
    def complete_task(self, task_id: int, actor_id: int) -> bool:
        """Mark a task complete.

        @requires task exists and is not complete
        @requires actor is the assignee or a leader
        @ensures is_complete is set
        @ensures task kept, not deleted
        @return bool
        """
        task = self._existing(task_id)
        if task["is_complete"]:
            raise ValueError("task is already complete")
        bucket_id = self.bucket_of(task_id)
        if not self.buckets.has_permission(bucket_id, actor_id, "complete"):
            raise PermissionError(f"user {actor_id} may not complete tasks here")
        is_leader = self.buckets.get_member_role(bucket_id, actor_id) == "LEADER"
        if not (is_leader or task["user_id"] == actor_id):
            raise PermissionError("only the assignee or a leader can complete a task")
        self.db.execute("UPDATE tasks SET is_complete = 1 WHERE task_id = ?", (task_id,))
        return True