<?php
// Shared PDO connection to the same SQLite file the Python backend uses.
function get_db() {
    $dbPath = __DIR__ . '/../backend/database/bucketlist.db';
    if (!file_exists($dbPath)) {
        die('Database not found. Run: python backend/database/init_db.py');
    }
    $db = new PDO('sqlite:' . $dbPath);
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    $db->exec('PRAGMA foreign_keys = ON');
    return $db;
}