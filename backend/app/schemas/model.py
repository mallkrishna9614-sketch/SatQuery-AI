from typing import Any, Literal

from pydantic import BaseModel, Field


EvidenceType = Literal[
    "visual",
    "scene",
    "spatial",
    "temporal",
    "cross_modal"
]


class BoundingBox(BaseModel):
    """
    Pixel-space bounding box.

    Coordinates follow:
        x, y = top-left corner
        width, height = box dimensions
    """

    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)


class GroundingRegion(BaseModel):
    """
    Region returned by a grounding or change model.
    """

    region_id: str

    bbox: BoundingBox

    label: str | None = None

    score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class EvidenceItem(BaseModel):

    type: EvidenceType

    description: str

    source: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class ModelResult(BaseModel):

    success: bool

    task_id: str

    task_type: str

    model_name: str

    model_version: str

    result: dict[str, Any] | None = None

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0
    )

    evidence: list[EvidenceItem] = Field(
        default_factory=list
    )

    error: str | None = None