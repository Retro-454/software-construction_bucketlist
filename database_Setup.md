# Project layout

```
.
├── backend/                 Python backend
│   ├── database/
│   │   ├── schema.sql       table definitions (committed)
│   │   ├── init_db.py       creates the local DB on first run
│   │   └── bucketlist.db    generated locally, git-ignored
│   └── requirements.txt
├── frontend/                PHP frontend
│   └── db.php               PDO connection to the same SQLite file
├── .gitignore
└── DATABASE_SETUP.md
```

# Database setup

The project uses **SQLite**: free, no server to install, and the whole database is one local file.

## First-time setup
1. Install Python 3.8+ and PHP 8+ with the SQLite extension.
   - Windows (XAMPP/php.net): enable `extension=pdo_sqlite` and `extension=sqlite3` in `php.ini`.
   - Ubuntu/Debian: `sudo apt install php-sqlite3`
   - macOS (Homebrew PHP): already included.
2. From the repo root, run:
   ```
   python backend/database/init_db.py
   ```
   This creates `backend/database/bucketlist.db` from `schema.sql`. Re-running it is safe.
3. To wipe and rebuild: `python backend/database/init_db.py --reset`

## Using it
- Python (from inside `backend/`): `from database.init_db import get_connection`
- PHP: `require __DIR__ . '/db.php'; $db = get_db();`

## Changing the schema
Edit `backend/database/schema.sql`, commit it, then teammates run
`python backend/database/init_db.py --reset` (or `ALTER TABLE` by hand to keep their data).
The `.db` file itself is never committed.