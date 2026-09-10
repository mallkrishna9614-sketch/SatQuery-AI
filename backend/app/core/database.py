import sqlite3
from pathlib import Path

from app.core.config import settings


# -----------------------------
# Database path
# -----------------------------

DATABASE_PATH = (
    Path(settings.DATA_DIR)
    / "satquery.db"
)


# -----------------------------
# Get database connection
# -----------------------------

def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# -----------------------------
# Initialize database
# -----------------------------

def init_database():

    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = get_connection()

    # -----------------------------
    # Images table
    # -----------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS images (
            image_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            modality TEXT NOT NULL,
            file_path TEXT NOT NULL,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            bands INTEGER NOT NULL,
            dtype TEXT NOT NULL,
            crs TEXT,
            resolution_x REAL,
            resolution_y REAL,
            bounds TEXT NOT NULL,
            transform TEXT NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # -----------------------------
    # Investigations table
    # -----------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS investigations (
            investigation_id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            status TEXT NOT NULL,
            tasks TEXT NOT NULL,
            execution TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()