"""
Database access layer.

Uses PyMySQL (raw SQL) against the exact table/column names defined in
schema.sql, so no separate ORM model layer is needed — schema.sql IS the
single source of truth for the data model.
"""
import json
import pymysql
import pymysql.cursors

from contextlib import contextmanager

from config import Config


def _connect(with_database=True):
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME if with_database else None,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        charset="utf8mb4",
    )


@contextmanager
def transaction():
    """
    Context manager providing an atomic transaction with a dict cursor.
    Commits on normal exit, rolls back on exception.
    """
    conn = _connect()
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """
    Execute schema.sql against the MySQL server to create the database,
    all 27 tables, and the seed data. Safe to re-run (schema.sql uses
    CREATE TABLE IF NOT EXISTS / INSERT IGNORE).
    """
    with open(Config.SCHEMA_PATH, "r", encoding="utf-8") as f:
        sql_script = f.read()

    conn = _connect(with_database=False)
    try:
        with conn.cursor() as cursor:
            for statement in sql_script.split(";"):
                stmt = statement.strip()
                if stmt:
                    cursor.execute(stmt)
        conn.commit()
    finally:
        conn.close()


def fetch_all(query, params=None):
    """Run a SELECT and return a list of dict rows."""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchall()
    finally:
        conn.close()


def fetch_one(query, params=None):
    """Run a SELECT and return a single dict row (or None)."""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchone()
    finally:
        conn.close()


def execute(query, params=None):
    """Run an INSERT/UPDATE/DELETE. Returns (last_insert_id, row_count)."""
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            conn.commit()
            return cur.lastrowid, cur.rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_many(statements_with_params):
    """
    Run several statements as ONE transaction.
    statements_with_params: list of (query, params) tuples.
    Returns the last statement's lastrowid.
    """
    conn = _connect()
    try:
        last_id = None
        with conn.cursor() as cur:
            for query, params in statements_with_params:
                cur.execute(query, params or ())
                last_id = cur.lastrowid
        conn.commit()
        return last_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def log_audit(user_id, entity_name, entity_id, action, old_val=None, new_val=None, ip_address: str | None = "0.0.0.0", user_agent: str | None = ""):
    """Insert an immutable record into the AuditLog table."""
    try:
        old_json = json.dumps(old_val) if old_val is not None else None
        new_json = json.dumps(new_val) if new_val is not None else None
        valid_actions = {'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'VIEW', 'EXPORT'}
        act = action if action in valid_actions else 'UPDATE'
        execute(
            """INSERT INTO AuditLog (userId, entityName, entityId, action, oldValue, newValue, ipAddress)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (user_id, entity_name, entity_id, act, old_json, new_json, ip_address or "0.0.0.0"),
        )
    except Exception as e:
        print(f"[WARN] Failed to write audit log: {e}")

