"""Postgres repository: the ONLY module that talks to the database.

Routes in main.py call these functions and never see SQL.
Swapping storage (SQLite in A2 -> Postgres here) touches only this file.
"""

import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()  # reads .env locally; inside Docker, compose supplies the env vars


def get_connection() -> psycopg.Connection:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and fill it in."
        )
    return psycopg.connect(url, row_factory=dict_row)


def init_db() -> None:
    """Create the tasks table if missing; seed 3 tasks only if the table is empty."""
    # `with connect()` commits on success and closes the connection on exit.
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id    SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done  BOOLEAN NOT NULL DEFAULT FALSE
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) AS n FROM tasks").fetchone()["n"]
        if count == 0:
            conn.cursor().executemany(
                "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                [
                    ("Buy groceries", False),
                    ("Read PostgreSQL documentation", False),
                    ("Complete Backend Assignment", True),
                ],
            )


def list_tasks() -> list[dict]:
    with get_connection() as conn:
        return conn.execute("SELECT id, title, done FROM tasks ORDER BY id").fetchall()


def get_task(task_id: int) -> dict | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = %s", (task_id,)
        ).fetchone()


def create_task(title: str) -> dict:
    with get_connection() as conn:
        return conn.execute(
            "INSERT INTO tasks (title, done) VALUES (%s, FALSE) "
            "RETURNING id, title, done",
            (title,),
        ).fetchone()


def update_task(task_id: int, title: str | None, done: bool | None) -> dict | None:
    """Partial update. None means 'leave this field unchanged'. Returns None if id unknown."""
    with get_connection() as conn:
        return conn.execute(
            """
            UPDATE tasks
               SET title = COALESCE(%s::text, title),
                   done  = COALESCE(%s::boolean, done)
             WHERE id = %s
            RETURNING id, title, done
            """,
            (title, done, task_id),
        ).fetchone()


def delete_task(task_id: int) -> bool:
    """Returns True if a row was deleted, False if the id was unknown."""
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        return cur.rowcount == 1
