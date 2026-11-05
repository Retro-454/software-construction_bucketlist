"""Category: a section of a bucket and its task list (SDD contract 10)."""
from __future__ import annotations

from abstract_manager import AbstractManager

SORT_ORDER = {  # whitelist: criterion -> ORDER BY clause
    "PRIORITY": "t.urgency DESC, t.task_id",
    "DUEDATE": "t.due_date IS NULL, t.due_date, t.task_id",
    "COMPLETION_STATUS": "t.is_complete, t.task_id",
}


class Category(AbstractManager):
    TABLE = "categories"
    PK = "category_id"
    COLUMNS = ("bucket_id", "category_name")
    UPDATABLE = ("category_name",)
    REQUIRED = ("bucket_id", "category_name")

    def __init__(self, db, buckets):
        super().__init__(db)
        self.buckets = buckets  # Bucket manager, for permission checks

    def bucket_of(self, category_id: int):
        rows = self.db.execute(
            "SELECT bucket_id FROM categories WHERE category_id = ?", (category_id,))
        return rows[0]["bucket_id"] if rows else None

    def can_perform(self, action, actor_id, record_id=None, data=None):
        if action == "create":
            bucket_id = (data or {}).get("bucket_id")
            needed = "create_category"
        else:
            bucket_id = self.bucket_of(record_id)
            needed = {"read": "view", "update": "edit", "delete": "delete"}[action]
        if bucket_id is None:
            return False
        return self.buckets.has_permission(bucket_id, actor_id, needed)

    # ---- contract 10: Task List and Progress ---------------------------
    def list_tasks(self, category_id: int, criterion: str, actor_id: int) -> list[dict]:
        """Return the category's tasks sorted by a criterion, each with its subtasks.

        @requires category exists and actor_id may view it
        @requires criterion is "PRIORITY", "DUEDATE" or "COMPLETION_STATUS"
        @ensures tasks sorted by the criterion
        @ensures no tasks lost or duplicated
        @return list[dict]
        """
        if criterion not in SORT_ORDER:
            raise ValueError(f"criterion must be one of {sorted(SORT_ORDER)}")
        if self._fetch(category_id) is None:
            raise LookupError(f"categories {category_id} not found")
        self._require("read", actor_id, category_id)

        rows = self.db.execute(
            "SELECT t.*, u.username AS assignee_name FROM tasks t "
            "LEFT JOIN users u ON u.user_id = t.user_id "
            f"WHERE t.category_id = ? ORDER BY {SORT_ORDER[criterion]}",
            (category_id,))
        subtasks: dict = {}
        for row in rows:
            if row["parent_task_id"] is not None:
                subtasks.setdefault(row["parent_task_id"], []).append(row)
        tasks = [r for r in rows if r["parent_task_id"] is None]
        for task in tasks:
            task["subtasks"] = subtasks.get(task["task_id"], [])
        return tasks

    def get_progress(self, category_id: int, actor_id: int) -> dict:
        """Report the category's progress (top-level tasks only).

        @requires category exists and actor_id may view it
        @ensures returns total and completed task counts
        @return dict
        """
        if self._fetch(category_id) is None:
            raise LookupError(f"categories {category_id} not found")
        self._require("read", actor_id, category_id)
        row = self.db.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(is_complete), 0) AS completed "
            "FROM tasks WHERE category_id = ? AND parent_task_id IS NULL",
            (category_id,))[0]
        return {"total": row["total"], "completed": row["completed"]}