import datetime as dt
from dataclasses import dataclass
from sqlite3 import Connection
from typing import Optional

from .utils import get_utc_timestamp_now


@dataclass(frozen=True)
class TeamRow:
    """
    Single row of Team from teams table
    """

    id: int
    title: str
    link: str
    last_approved: int


def init_table(conn: Connection):
    """
    Create table if not exists
    """

    c = conn.cursor()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            title TEXT NOT NULL,
            link TEXT NOT NULL,
            last_approved INTEGER NOT NULL
        );
    """)
    conn.commit()
    conn.execute("""
        CREATE INDEX IF NOT EXISTS ix_teams_title ON teams (title);
    """)
    conn.commit()
    c.close()


def insert(conn: Connection, title: str, link: str) -> int:
    """
    Insert new row. id and last_approved are autogenerated.
    :return id of created row.
    """

    last_approved = int(get_utc_timestamp_now())

    c = conn.cursor()
    c.execute("""
        INSERT INTO teams (title, link, last_approved) VALUES (?, ?, ?);
    """, (title, link, last_approved))
    conn.commit()
    c.close()
    return c.lastrowid


def get_by_title(conn: Connection, title: str) -> Optional[TeamRow]:
    """
    Get a row by teams.title
    """

    c = conn.cursor()
    c.execute("""
        SELECT * FROM teams WHERE title = ? LIMIT 1;
    """, (title,))
    result = c.fetchone()
    c.close()
    if result:
        return TeamRow(*result)
    return None


def get_by_id(conn: Connection, id_: int):
    """
    Get a row by teams.id
    """

    c = conn.cursor()
    c.execute("""
            SELECT * FROM teams WHERE id = ? LIMIT 1;
        """, (id_,))
    result = c.fetchone()
    c.close()
    return result


def approve_team(conn: Connection, id_: int):
    """
    Set teams.last_approved time to now.
    It means that you have checked the team.link, and it is correct.
    """

    now = int(get_utc_timestamp_now())
    c = conn.cursor()
    c.execute("""
        UPDATE teams SET last_approved = ? WHERE id = ?;
    """, (now, id_))
    conn.commit()
    c.close()


def get_all_teams(conn: Connection) -> list[TeamRow]:
    c = conn.cursor()
    c.execute("""
        SELECT * FROM teams;
    """)
    result = [TeamRow(*row) for row in c.fetchall()]
    c.close()
    return result

