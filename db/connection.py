import sqlite3

from config import DB_PATH
from .tables import teams


def connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def init_all():
    """
    Init every table
    """

    conn = connect()

    teams.init_table(conn)

    conn.close()
