from pathlib import Path
import math

import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject

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

    except SatQueryError:
        raise

    except Exception as exc:

        raise SatQueryError(
            "INVALID_RASTER",
            "The uploaded file could not be opened as a valid raster.",
            {
                "reason": str(exc)
            }
        )


# =================================================
# GeoTIFF processing / co-registration foundation
# =================================================

def is_same_grid(
    reference_path: Path,
    source_path: Path
) -> bool:

    try:

        with rasterio.open(reference_path) as reference:
            with rasterio.open(source_path) as source:

                return (
                    reference.crs == source.crs
                    and reference.width == source.width
                    and reference.height == source.height
                    and reference.transform == source.transform
                )

    except Exception as exc:

        raise SatQueryError(
            "RASTER_GRID_CHECK_FAILED",
            "Unable to compare raster grids.",
            {
                "reason": str(exc)
            }
        )


def align_to_reference(
    source_path: Path,
    reference_path: Path,
    output_path: Path,
    resampling_method: str = "bilinear"
) -> Path:

    """
    Align a source GeoTIFF to the exact grid of a reference GeoTIFF.

    The output uses the reference raster's:
        - CRS
        - width
        - height
        - transform

    This provides the spatial-alignment foundation required
    for temporal and optical-SAR analysis.
    """

    # -----------------------------
    # 1. Validate paths
    # -----------------------------

    if not source_path.exists():
        raise SatQueryError(
            "SOURCE_RASTER_NOT_FOUND",
            "Source raster does not exist.",
            {
                "path": str(source_path)
            }
        )

    if not reference_path.exists():
        raise SatQueryError(
            "REFERENCE_RASTER_NOT_FOUND",
            "Reference raster does not exist.",
            {
                "path": str(reference_path)
            }
        )

    # -----------------------------
    # 2. Select resampling method
    # -----------------------------

    resampling_methods = {
        "nearest": Resampling.nearest,
        "bilinear": Resampling.bilinear,
        "cubic": Resampling.cubic
    }

    if resampling_method not in resampling_methods:

        raise SatQueryError(
            "INVALID_RESAMPLING_METHOD",
            "Unsupported raster resampling method.",
            {
                "method": resampling_method,
                "allowed": sorted(
                    resampling_methods.keys()
                )
            }
        )

    resampling = resampling_methods[
        resampling_method
    ]

    # -----------------------------
    # 3. Open source/reference
    # -----------------------------

    try:

        with rasterio.open(source_path) as source:

            with rasterio.open(reference_path) as reference:

                # Both rasters need CRS information
                if source.crs is None:

                    raise SatQueryError(
                        "SOURCE_CRS_MISSING",
                        "Source raster does not contain a CRS."
                    )

                if reference.crs is None:

                    raise SatQueryError(
                        "REFERENCE_CRS_MISSING",
                        "Reference raster does not contain a CRS."
                    )

                # -----------------------------
                # 4. Build output profile
                # -----------------------------

                profile = source.profile.copy()

                profile.update(
                    driver="GTiff",
                    width=reference.width,
                    height=reference.height,
                    crs=reference.crs,
                    transform=reference.transform
                )

                output_path.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                # -----------------------------
                # 5. Reproject/resample
                # -----------------------------

                with rasterio.open(
                    output_path,
                    "w",
                    **profile
                ) as destination:

                    for band_index in range(
                        1,
                        source.count + 1
                    ):

                        reproject(
                            source=rasterio.band(
                                source,
                                band_index
                            ),

                            destination=rasterio.band(
                                destination,
                                band_index
                            ),

                            src_transform=source.transform,
                            src_crs=source.crs,

                            dst_transform=reference.transform,
                            dst_crs=reference.crs,

                            resampling=resampling
                        )

        return output_path

    except SatQueryError:
        raise

    except Exception as exc:

        output_path.unlink(
            missing_ok=True
        )

        raise SatQueryError(
            "RASTER_ALIGNMENT_FAILED",
            "Unable to align raster to the reference grid.",
            {
                "reason": str(exc)
            }
        )


def validate_aligned_pair(
    reference_path: Path,
    aligned_path: Path
) -> bool:

    """
    Verify that two GeoTIFFs use the same spatial grid.
    """

    try:

        with rasterio.open(reference_path) as reference:

            with rasterio.open(aligned_path) as aligned:

                return (
                    reference.crs == aligned.crs
                    and reference.width == aligned.width
                    and reference.height == aligned.height
                    and reference.transform == aligned.transform
                )

    except Exception as exc:

        raise SatQueryError(
            "RASTER_ALIGNMENT_VALIDATION_FAILED",
            "Unable to validate aligned rasters.",
            {
                "reason": str(exc)
            }
        )
def needs_alignment(
    reference_path: Path,
    source_path: Path
) -> bool:
    """
    Return True when the source raster does not match
    the exact spatial grid of the reference raster.
    """

    return not is_same_grid(
        reference_path=reference_path,
        source_path=source_path
    )