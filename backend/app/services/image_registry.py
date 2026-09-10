import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.database import get_connection
from app.schemas.image import RasterMetadata


def register_image(
    metadata: RasterMetadata,
    file_path: Path
):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO images (
            image_id,
            filename,
            modality,
            file_path,
            width,
            height,
            bands,
            dtype,
            crs,
            resolution_x,
            resolution_y,
            bounds,
            transform,
            file_size_bytes,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            metadata.image_id,
            metadata.filename,
            metadata.modality,
            str(file_path),
            metadata.width,
            metadata.height,
            metadata.bands,
            metadata.dtype,
            metadata.crs,
            metadata.resolution_x,
            metadata.resolution_y,
            json.dumps(metadata.bounds),
            json.dumps(metadata.transform),
            metadata.file_size_bytes,
            datetime.now(timezone.utc).isoformat()
        )
    )

    connection.commit()
    connection.close()


def get_image(
    image_id: str
):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM images
        WHERE image_id = ?
        """,
        (image_id,)
    ).fetchone()

    connection.close()

    return row