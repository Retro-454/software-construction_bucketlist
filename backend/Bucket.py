"""Bucket: a project, its members and their roles (SDD contract 9: Roles and Permissions).

Bridging technique: Pseudocode Programming Process (PPP). Each public routine was
first written as pseudocode (see the SDD, Bucket section). Each pseudocode line
became a comment below, and the code was written under its comment.
"""
from __future__ import annotations

from abstract_manager import AbstractManager

LEADER_ONLY_ACTIONS = {"edit", "delete", "create_category", "create_task", "manage_members"}
MEMBER_ACTIONS = {"view", "add_note", "add_subtask", "complete"}
ALL_ACTIONS = LEADER_ONLY_ACTIONS | MEMBER_ACTIONS


class Bucket(AbstractManager):
    TABLE = "buckets"
    PK = "bucket_id"
    COLUMNS = ("bucket_name", "progress_summary")
    REQUIRED = ("bucket_name",)

    def can_perform(self, action, actor_id, record_id=None, data=None):
        if action == "create":
            return bool(self.db.execute(
                "SELECT 1 FROM users WHERE user_id = ?", (actor_id,)))
        needed = {"read": "view", "update": "edit", "delete": "delete"}[action]
        return self.has_permission(record_id, actor_id, needed)

    def create(self, data: dict, actor_id: int) -> int:
        """Create a bucket; its creator becomes its first leader."""
        # Store the new bucket using the inherited create
        # (validates fields and checks that the creator exists).
        bucket_id = super().create(data, actor_id)
        try:
            # Add the creator to the bucket's members with the role leader.
            self.db.execute(
                "INSERT INTO bucket_members (bucket_id, user_id, role) "
                "VALUES (?, ?, 'leader')", (bucket_id, actor_id))
        except Exception:
            # If that fails, delete the new bucket so no bucket is left
            # without a leader, and report the error.
            self.db.execute("DELETE FROM buckets WHERE bucket_id = ?", (bucket_id,))
            raise
        # Return the new bucket's ID.
        return bucket_id

    # -- contract 9: Roles and Permissions --
    def get_member_role(self, bucket_id: int, user_id: int) -> str:
        """Report a user's role in the bucket: "LEADER", "MEMBER", or "NONE"."""
        # If the bucket ID or user ID is missing, report an invalid-input error.
        if bucket_id is None or user_id is None:
            raise ValueError("bucket_id and user_id must be provided")
        # Look up the user's membership row for this bucket.
        rows = self.db.execute(
            "SELECT role FROM bucket_members WHERE bucket_id = ? AND user_id = ?",
            (bucket_id, user_id))
        # If a row exists, return its role in capitals; otherwise return "NONE".
        return rows[0]["role"].upper() if rows else "NONE"

    def has_permission(self, bucket_id: int, user_id: int, action: str) -> bool:
        """Report whether a user may perform an action in the bucket."""
        # Get the user's role in the bucket.
        role = self.get_member_role(bucket_id, user_id)
        # A leader may perform any known action.
        if role == "LEADER":
            return action in ALL_ACTIONS
        # A member may perform only member actions.
        if role == "MEMBER":
            return action in MEMBER_ACTIONS
        # Anyone else is denied.
        return False

    def add_member(self, bucket_id: int, user_id: int, role: str, actor_id: int) -> bool:
        """Add a user to the bucket, or change their role (leaders only)."""
        # Normalize the role; if it is not leader or member, report an invalid-input error.
        role = role.lower() if isinstance(role, str) else role
        if role not in ("leader", "member"):
            raise ValueError('role must be "leader" or "member"')
        # If the bucket does not exist, report not found.
        if self._fetch(bucket_id) is None:
            raise LookupError(f"buckets {bucket_id} not found")
        # If the actor may not manage members, report a permission error.
        if not self.has_permission(bucket_id, actor_id, "manage_members"):
            raise PermissionError(f"user {actor_id} may not manage members")
        # Insert the membership, or update the role if the user is already a member.
        self.db.execute(
            "INSERT INTO bucket_members (bucket_id, user_id, role) VALUES (?, ?, ?) "
            "ON CONFLICT(bucket_id, user_id) DO UPDATE SET role = excluded.role",
            (bucket_id, user_id, role))
        # Report success.
        return True
