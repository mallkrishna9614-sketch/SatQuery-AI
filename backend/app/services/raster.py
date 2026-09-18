from pathlib import Path
import math

import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject
from PIL import Image

from app.core.errors import SatQueryError
from app.schemas.image import RasterMetadata


# Geospatial raster formats used by SatQuery.
ALLOWED_EXTENSIONS = {
    ".tif",
    ".tiff"
}

# Standard image formats supported for VLM/public-benchmark inference.
STANDARD_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg"
}


def inspect_raster(
    image_id: str,
    path: Path,
    filename: str,
    modality: str
) -> RasterMetadata:

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise SatQueryError(
            "UNSUPPORTED_FORMAT",
            "Only GeoTIFF/TIFF imagery is accepted by the raster inspector.",
            {
                "filename": filename,
                "allowed": sorted(ALLOWED_EXTENSIONS)
            }
        )

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
            {"reason": str(exc)}
        )


def inspect_standard_image(
    image_id: str,
    path: Path,
    filename: str,
    modality: str
) -> RasterMetadata:
    """
    Inspect PNG/JPEG imagery used by VLMs and prescribed
    public benchmark inputs.

    Standard images do not carry the geospatial metadata
    required for CRS/overlap/grid analysis, so those fields
    are intentionally empty rather than fabricated.
    """

    if path.suffix.lower() not in STANDARD_IMAGE_EXTENSIONS:
        raise SatQueryError(
            "UNSUPPORTED_FORMAT",
            "Only PNG/JPEG standard images are accepted here.",
            {
                "filename": filename,
                "allowed": sorted(STANDARD_IMAGE_EXTENSIONS)
            }
        )

    try:
        with Image.open(path) as image:
            image.verify()

        with Image.open(path) as image:
            width, height = image.size
            bands = len(image.getbands())
            dtype_by_mode = {
                "1": "uint1",
                "L": "uint8",
                "LA": "uint8",
                "P": "uint8",
                "RGB": "uint8",
                "RGBA": "uint8",
                "I": "int32",
                "F": "float32",
                "I;16": "uint16"
            }

            return RasterMetadata(
                image_id=image_id,
                filename=filename,
                modality=modality,
                width=width,
                height=height,
                bands=bands,
                dtype=dtype_by_mode.get(image.mode, image.mode),
                crs=None,
                resolution_x=None,
                resolution_y=None,
                bounds=[],
                transform=[],
                file_size_bytes=path.stat().st_size
            )

    except SatQueryError:
        raise

    except Exception as exc:
        raise SatQueryError(
            "INVALID_IMAGE",
            "The uploaded file is not a valid readable PNG/JPEG image.",
            {"reason": str(exc)}
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
            {"reason": str(exc)}
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

    if not source_path.exists():
        raise SatQueryError(
            "SOURCE_RASTER_NOT_FOUND",
            "Source raster does not exist.",
            {"path": str(source_path)}
        )

    if not reference_path.exists():
        raise SatQueryError(
            "REFERENCE_RASTER_NOT_FOUND",
            "Reference raster does not exist.",
            {"path": str(reference_path)}
        )

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
                "allowed": sorted(resampling_methods.keys())
            }
        )

    resampling = resampling_methods[resampling_method]

    try:
        with rasterio.open(source_path) as source:
            with rasterio.open(reference_path) as reference:

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
        output_path.unlink(missing_ok=True)

        raise SatQueryError(
            "RASTER_ALIGNMENT_FAILED",
            "Unable to align raster to the reference grid.",
            {"reason": str(exc)}
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
            {"reason": str(exc)}
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
