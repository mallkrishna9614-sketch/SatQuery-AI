from pathlib import Path
import math

import rasterio

from app.core.errors import SatQueryError
from app.schemas.image import RasterMetadata


# Only these formats are allowed
ALLOWED_EXTENSIONS = {
    ".tif",
    ".tiff"
}


def inspect_raster(
    image_id: str,
    path: Path,
    filename: str,
    modality: str
) -> RasterMetadata:

    # -----------------------------
    # 1. Check file extension
    # -----------------------------
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise SatQueryError(
            "UNSUPPORTED_FORMAT",
            "Only GeoTIFF/TIFF imagery is accepted.",
            {
                "filename": filename,
                "allowed": sorted(ALLOWED_EXTENSIONS)
            }
        )

    # -----------------------------
    # 2. Open raster
    # -----------------------------
    try:

        with rasterio.open(path) as src:

            transform = src.transform

            resolution_x, resolution_y = src.res

            bounds = [
                src.bounds.left,
                src.bounds.bottom,
                src.bounds.right,
                src.bounds.top
            ]

            # CRS can sometimes be missing
            crs = (
                src.crs.to_string()
                if src.crs
                else None
            )

            return RasterMetadata(

                image_id=image_id,

                filename=filename,

                modality=modality,

                width=src.width,

                height=src.height,

                bands=src.count,

                dtype=str(src.dtypes[0]),

                crs=crs,

                resolution_x=(
                    float(resolution_x)
                    if math.isfinite(resolution_x)
                    else None
                ),

                resolution_y=(
                    float(abs(resolution_y))
                    if math.isfinite(resolution_y)
                    else None
                ),

                bounds=bounds,

                transform=[
                    transform.a,
                    transform.b,
                    transform.c,
                    transform.d,
                    transform.e,
                    transform.f
                ],

                file_size_bytes=path.stat().st_size
            )

    except Exception as exc:

        raise SatQueryError(
            "INVALID_RASTER",
            "The uploaded file could not be opened as a valid raster.",
            {
                "reason": str(exc)
            }
        )