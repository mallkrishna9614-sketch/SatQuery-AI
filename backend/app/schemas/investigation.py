from typing import Literal

from pydantic import BaseModel, Field


# -----------------------------
# Investigation task
# -----------------------------

TaskType = Literal[
    "vqa",
    "caption",
    "grounding",
    "change_analysis",
    "optical_sar_fusion"
]


class InvestigationTask(BaseModel):
    task_id: str

    task_type: TaskType

    image_ids: list[str] = Field(
        min_length=1
    )

    query: str | None = None

    parameters: dict = Field(
        default_factory=dict
    )


# -----------------------------
# Investigation request
# -----------------------------

class InvestigationRequest(BaseModel):

    query: str = Field(
        min_length=3,
        max_length=2000
    )

    image_ids: list[str] = Field(
        min_length=1,
        max_length=4
    )


# -----------------------------
# Investigation response
# -----------------------------

class InvestigationResponse(BaseModel):

    investigation_id: str

    status: Literal[
        "queued",
        "running",
        "completed",
        "failed"
    ]

    query: str

    tasks: list[InvestigationTask]

    message: str