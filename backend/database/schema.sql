-- Bucket List database schema (SQLite)
-- Safe to run more than once: every statement uses IF NOT EXISTS.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL            -- never store plain passwords
);

CREATE TABLE IF NOT EXISTS buckets (
    bucket_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    bucket_name       TEXT NOT NULL,
    progress_summary  TEXT
);

-- Replaces user.buckets and Bucket.leaders: one row per user per bucket,
-- and the role decides leader vs member access.
CREATE TABLE IF NOT EXISTS bucket_members (
    bucket_id  INTEGER NOT NULL REFERENCES buckets(bucket_id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(user_id)     ON DELETE CASCADE,
    role       TEXT NOT NULL CHECK (role IN ('leader', 'member')),
    PRIMARY KEY (bucket_id, user_id)
);

-- Replaces Bucket.categories (a category belongs to one bucket).
CREATE TABLE IF NOT EXISTS categories (
    category_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    bucket_id            INTEGER NOT NULL REFERENCES buckets(bucket_id) ON DELETE CASCADE,
    category_name        TEXT NOT NULL,
    completed_task_num   INTEGER NOT NULL DEFAULT 0
);

-- Replaces Categories.members and user.categories (many members per category).
CREATE TABLE IF NOT EXISTS category_members (
    category_id  INTEGER NOT NULL REFERENCES categories(category_id) ON DELETE CASCADE,
    user_id      INTEGER NOT NULL REFERENCES users(user_id)          ON DELETE CASCADE,
    PRIMARY KEY (category_id, user_id)
);

-- Replaces Categories.tasks and user.tasks.
CREATE TABLE IF NOT EXISTS tasks (
    task_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id       INTEGER NOT NULL REFERENCES categories(category_id) ON DELETE CASCADE,
    user_id           INTEGER REFERENCES users(user_id) ON DELETE SET NULL,  -- assignee
    task_name         TEXT NOT NULL,
    task_description  TEXT,
    due_date          TEXT,                         -- ISO format: YYYY-MM-DD
    notes             TEXT,
    parent_task_id    INTEGER REFERENCES tasks(task_id) ON DELETE CASCADE,   -- subtask link
    urgency           INTEGER NOT NULL DEFAULT 0,
    is_on_hold        INTEGER NOT NULL DEFAULT 0 CHECK (is_on_hold IN (0, 1)),
    is_complete       INTEGER NOT NULL DEFAULT 0 CHECK (is_complete IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category_id);
CREATE INDEX IF NOT EXISTS idx_tasks_user     ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_parent   ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_members_user   ON bucket_members(user_id);