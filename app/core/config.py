# app/core/config.py

import os
from dotenv import load_dotenv

# Cargamos variables del .env
load_dotenv()

# Variables de entorno
DB_SERVER = os.getenv("DB_SERVER", "localhost\\SQLEXPRESS")
DB_NAME = os.getenv("DB_NAME", "raicesExtra")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_DRIVER = os.getenv("DB_DRIVER", "SQL Server")

