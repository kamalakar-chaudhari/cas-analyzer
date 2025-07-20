# utils/db_utils.py
import sqlite3

from config.constants import SQLITE_DB_PATH


def get_sqlite_connection():
    return sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
