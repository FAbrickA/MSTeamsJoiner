from . import tables
from . import connection

__all__ = [
    "tables",
    "connection",
]

connection.init_all()
