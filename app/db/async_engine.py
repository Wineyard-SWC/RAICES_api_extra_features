# app/db/async_engine.py
import ssl, pathlib, urllib.parse as up
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, AIVEN_CA_PEM
)

# URL sin sslmode
user = up.quote_plus(DB_USER)
pwd  = up.quote_plus(DB_PASSWORD)
DATABASE_URL = (
    f"postgresql+asyncpg://{user}:{pwd}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# contexto SSL estricto
ssl_ctx = ssl.create_default_context(
    cafile=str(pathlib.Path(AIVEN_CA_PEM))
)

engine_async = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=5,
    connect_args={"ssl": ssl_ctx},   # ← aquí va el contexto
)

AsyncSessionLocal = async_sessionmaker(engine_async, expire_on_commit=False)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
