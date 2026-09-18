from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.model import EvidenceItem, ModelResult


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
    image_ids: list[str] = Field(min_length=1)
    query: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class ConfidenceResult(BaseModel):
    task_id: str
    task_type: str
    model: dict[str, str]
    confidence: float = Field(ge=0.0, le=1.0)
    label: Literal["low", "medium", "high"]


class InvestigationExecution(BaseModel):
    model_results: list[ModelResult] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    confidence: list[ConfidenceResult] = Field(default_factory=list)
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    trace: list[dict[str, Any]] = Field(default_factory=list)
    change_analysis: dict[str, Any] | None = None

class InvestigationRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    image_ids: list[str] = Field(min_length=1, max_length=4)


class InvestigationFinding(BaseModel):
    summary: str
    task_type: str
    change_detected: bool | None = None
    change_type: str | None = None


class InvestigationResponse(BaseModel):
    investigation_id: str
    status: Literal["queued", "running", "completed", "failed"]
    query: str
    tasks: list[InvestigationTask]
    execution: InvestigationExecution | None = None
    finding: InvestigationFinding | None = None
    message: str