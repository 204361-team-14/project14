"""Migrate the old SQLite database.db into the new PostgreSQL database.

Usage:
    python scripts/migrate_sqlite_to_postgres.py path/to/database.db

Environment:
    DATABASE_URL=postgresql://cs_user:cs_password@localhost:5432/cs_building_services
"""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import psycopg

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://cs_user:cs_password@localhost:5432/cs_building_services",
)

TABLES = [
    "rooms",
    "service_requests",
    "request_history",
    "lost_found_items",
]


def sqlite_rows(conn, table):
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY id")]


def table_exists(conn, table):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def insert_rows(pg, table, rows):
    if not rows:
        return

    columns = list(rows[0].keys())
    placeholders = ", ".join(["%s"] * len(columns))
    column_sql = ", ".join(columns)
    update_columns = [col for col in columns if col != "id"]
    update_sql = ", ".join(f"{col}=EXCLUDED.{col}" for col in update_columns)

    sql = (
        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders}) "
        f"ON CONFLICT (id) DO UPDATE SET {update_sql}"
    )

    for row in rows:
        values = [row[col] for col in columns]
        pg.execute(sql, values)


def reset_sequence(pg, table):
    pg.execute(
        "SELECT setval(pg_get_serial_sequence(%s, 'id'), "
        "COALESCE((SELECT MAX(id) FROM " + table + "), 1), true)",
        (table,),
    )


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/migrate_sqlite_to_postgres.py path/to/database.db")

    sqlite_path = Path(sys.argv[1]).resolve()
    if not sqlite_path.exists():
        raise SystemExit(f"SQLite database not found: {sqlite_path}")

    sqlite_conn = sqlite3.connect(sqlite_path)

    with psycopg.connect(DATABASE_URL) as pg:
        for table in TABLES:
            if not table_exists(sqlite_conn, table):
                print(f"skip {table}: table not found")
                continue

            rows = sqlite_rows(sqlite_conn, table)

            # The new Lost & Found flow only displays found reports, but old rows are kept.
            if table == "rooms":
                for row in rows:
                    if "is_active" in row:
                        row["is_active"] = bool(row["is_active"])

            if table in {"service_requests", "lost_found_items"}:
                for row in rows:
                    image_path = row.get("image_path")
                    if image_path:
                        row["image_path"] = Path(image_path).name

            insert_rows(pg, table, rows)
            reset_sequence(pg, table)
            print(f"migrated {table}: {len(rows)} rows")

    sqlite_conn.close()
    print("Migration completed.")


if __name__ == "__main__":
    main()
