# app/db/connection.py

import pyodbc
from app.core.config import DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD, DB_DRIVER

def get_connection():
    """
    Retorna una nueva conexión a la base de datos usando pyodbc.
    """
    connection_string = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD}"
    )
    conn = pyodbc.connect(connection_string)
    return conn
