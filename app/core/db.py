# app/core/db.py
"""
Single shared, pooled database engine for the entire application.



Usage:
    from app.core.db import engine
    from sqlalchemy import text

    with engine.connect() as conn:
        rows = conn.execute(text("SELECT ..."), {"param": value}).mappings().all()

    with engine.begin() as conn:               # auto commit/rollback
        conn.execute(text("INSERT ..."), {...})
"""

import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
logger = logging.getLogger(__name__)

DB_URL = os.getenv("DATABASE_URL", "")
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

if not DB_URL:
    logger.warning("⚠️ DATABASE_URL is not set — DB calls will fail until it is configured.")

# pool_pre_ping avoids handing out dead connections after Neon idles them out.
# pool_size/max_overflow are conservative defaults for a small deployment;
# tune upward once real concurrency numbers are known.
engine = create_engine(
    DB_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
)


def get_vector_connection():
    """
    Returns a pooled raw DBAPI (psycopg2) connection with pgvector's numpy/list
    adapters registered.

    pgvector's register_vector() only understands psycopg2 connections, not a
    SQLAlchemy Engine/Connection — so the two modules that do ANN vector search
    (app/core/ingest_pdfs.py, app/core/search.py) use this helper instead of
    plain `engine.connect()`. It still checks the connection out of the shared
    pool via `engine.raw_connection()`, so it gets the same pooling benefit as
    everywhere else — the caller just needs to call `.close()` (which returns
    it to the pool) when done, same as any other pooled connection.
    """
    from pgvector.psycopg2 import register_vector

    conn = engine.raw_connection()
    register_vector(conn)
    return conn
