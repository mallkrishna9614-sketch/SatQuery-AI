import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from rasterio.errors import RasterioIOError

from app.core.config import settings
from app.core.errors import SatQueryError
from app.schemas.image import ImageUploadResponse
from app.services.raster import inspect_raster
from app.services.image_registry import register_image


router = APIRouter(
    prefix="/images",
    tags=["images"]
)


@router.post(
    "/upload",
    response_model=ImageUploadResponse
)
async def upload_image(
    file: UploadFile = File(...),
    modality: str = Form(...)
):

    # -------------------------------------------------
    # 1. Validate modality
    # -------------------------------------------------

    if modality not in {
        "optical",
        "multispectral",
        "sar"
    }:
        raise SatQueryError(
            "INVALID_MODALITY",
            "Modality must be optical, multispectral or sar."
        )

    # -------------------------------------------------
    # 2. Validate file format
    # -------------------------------------------------

    suffix = Path(
        file.filename or ""
    ).suffix.lower()

    if suffix not in {
        ".tif",
        ".tiff"
    }:
        raise SatQueryError(
            "UNSUPPORTED_FORMAT",
            "Only GeoTIFF/TIFF files are accepted."
        )

    # -------------------------------------------------
    # 3. Create image ID and target path
    # -------------------------------------------------

    image_id = (
        "img_"
        + uuid.uuid4().hex[:12]
    )

    target = (
        settings.upload_dir
        / f"{image_id}{suffix}"
    )

    # -------------------------------------------------
    # 4. Save uploaded file
    # -------------------------------------------------

    size = 0

    max_bytes = (
        settings.MAX_UPLOAD_MB
        * 1024
        * 1024
    )

    try:

        with target.open("wb") as output:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                size += len(chunk)

                if size > max_bytes:

                    target.unlink(
                        missing_ok=True
                    )

                    raise SatQueryError(
                        "FILE_TOO_LARGE",
                        (
                            "Maximum upload size is "
                            f"{settings.MAX_UPLOAD_MB} MB."
                        )
                    )

                output.write(chunk)

    except SatQueryError:
        raise

    except OSError as exc:

        target.unlink(
            missing_ok=True
        )

        raise SatQueryError(
            "FILE_SAVE_FAILED",
            "The uploaded file could not be saved.",
            details=str(exc),
            status_code=500
        )

    finally:

        await file.close()

    # -------------------------------------------------
    # 5. Inspect GeoTIFF
    # -------------------------------------------------

    try:

        metadata = inspect_raster(
            image_id=image_id,
            path=target,
            filename=file.filename or target.name,
            modality=modality
        )

    except (RasterioIOError, ValueError) as exc:

        target.unlink(
            missing_ok=True
        )

        raise SatQueryError(
            "INVALID_RASTER",
            "The uploaded file is not a valid readable GeoTIFF.",
            details=str(exc)
        )

    # -------------------------------------------------
    # 6. Register image in database
    # -------------------------------------------------

    try:

        register_image(
            metadata=metadata,
            file_path=target
        )

    except Exception as exc:

        target.unlink(
            missing_ok=True
        )

        raise SatQueryError(
            "IMAGE_REGISTRATION_FAILED",
            "The image could not be registered.",
            details=str(exc),
            status_code=500
        )

    # -------------------------------------------------
    # 7. Return metadata
    # -------------------------------------------------

    return ImageUploadResponse(
        image=metadata
    )