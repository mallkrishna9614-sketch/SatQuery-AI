from typing import Literal

from pydantic import BaseModel, Field


# Supported remote-sensing modalities
Modality = Literal[
    "optical",
    "multispectral",
    "sar"
]


class RasterMetadata(BaseModel):
    image_id: str
    filename: str

    modality: Modality

    # Raster information
    width: int
    height: int
    bands: int
    dtype: str

    # Geospatial information
    crs: str | None
    resolution_x: float | None
    resolution_y: float | None

    bounds: list[float]

    # Affine transform
    transform: list[float]

    # File information
    file_size_bytes: int


class ImageUploadResponse(BaseModel):
    image: RasterMetadata


class CompatibilityRequest(BaseModel):
    image_ids: list[str] = Field(
        min_length=1,
        max_length=4
    )

    check_type: Literal[
        "temporal",
        "optical_sar",
        "generic"
    ] = "generic"


class CompatibilityResponse(BaseModel):
    compatible: bool

    reasons: list[str]

    images: list[RasterMetadata]