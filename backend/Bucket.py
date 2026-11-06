"""Bucket: a project, its members and their roles (SDD contract 9 I believe it was)"""
from __future__ import annotations

from abstract_manager import AbstractManager
LEADER_ONLY_ACTIONS = {"edit", "delete", "create_category", "create_task", "manage_members"}
MEMBER_ACTIONS ={"view", "add_note", "add_subtask", "complete"}
ALL_ACTIONS = LEADER_ONLY_ACTIONS | MEMBER_ACTIONS

class Bucket(AbstractManager):
    TABLE = "buckets"
    PK = "bucket_id"
    COLUMNS = ("bucket_name", "progress_summary")
    REQUIRED = ("bucket_name",)

    def can_perform(self, action, actor_id, record_id=None, data=None):
        if action =="create":
            return bool(self.db.execute(
                "SELECT 1 FROM users WHERE user_id = ?", (actor_id,)))
        needed = {"read": "view", "update": "edit", "delete": "delete"}[action]
        return self.has_permission(record_id, actor_id, needed)

    def create(self, data: dict, actor_id: int) -> int:
        "create a bucket, creator becomes leader"
        bucket_id = super().create(data, actor_id)
        try:
            self.db.execute(
                "INSERT INTO bucket_members (bucket_id, user_id, role) "
                 "VALUES (?, ?, 'leader')", (bucket_id, actor_id))
        except Exception:
            self.db.execute("DELETE FROM buckets WHERE bucket_id = ?", (bucket_id,))
            raise
        return bucket_id
    #--contact 9: Roles and permissions
    def get_member_role(self, bucket_id: int, user_id: int) -> str:
        "Report user's role in bucket."
        "@requires bucket_id and user_id != None"
        "@ensures bucket unchanged"
        "@returns str"
        if bucket_id is None or user_id is None:
            raise ValueError("bucket_id and user_id must be provided")
        rows = self.db.execute(
            "SELECT role FROM bucket_members WHERE bucket_id = ? AND user_id = ?",
            (bucket_id, user_id))
        return rows[0]["role"].upper() if rows else None
    def add_member(self, bucket_id: int, user_id: int, role: str, actor_id: int) -> bool:
        """add a user to the bucket or change their role (leaders can only do this)
        @requires the bucket exists and role is "leader" or "member"
        @requires actor_id is a leader of the bucket
        @ensures user_id has exactly one membership row with that role
        @return bool
        """
        role = role.lower() if isinstance(role, str) else role
        if role not in ("leader", "member"):
            raise ValueError('role must be "leader" or "member"')
        if self._fetch(bucket_id) is None:
            raise LookupError(f"buckets {bucket_id} not found")
        if not self.has_permission(bucket_id, actor_id, "manage_members"):
            raise PermissionError(f"user {actor_id} may not manage members")
        self.db.execute(
            "INSERT INTO bucket_members (bucket_id, user_id, role) VALUES (?, ?, ?) "
            "ON CONFLICT(bucket_id, user_id) DO UPDATE SET role = excluded.role",
            (bucket_id, user_id, role))
        return True
    def has_permission(self, bucket_id: int, user_id: int, action: str) -> bool:
        role = self.get_member_role(bucket_id, user_id)

        if role is None:
            return False

        if role == "LEADER":
            return action in ALL_ACTIONS

        if role == "MEMBER":
            return action in MEMBER_ACTIONS

        return False