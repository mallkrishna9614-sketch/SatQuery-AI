from dataclasses import dataclass
from typing import Callable

from app.services.model_adapter import ModelAdapter


@dataclass
class ModelSpec:
    name: str
    task_type: str
    version: str
    description: str
    adapter: ModelAdapter | None = None
    handler: Callable | None = None


MODEL_REGISTRY: dict[str, ModelSpec] = {}


def register_model(
    name: str,
    task_type: str,
    version: str,
    description: str,
    adapter: ModelAdapter | None = None,
    handler: Callable | None = None,
):
    """
    Register a specialist model.

    A model can provide either:
        - adapter: real ML implementation
        - handler: temporary/mock implementation

    If both are provided, the execution engine
    prefers the real adapter.
    """

    MODEL_REGISTRY[task_type] = ModelSpec(
        name=name,
        task_type=task_type,
        version=version,
        description=description,
        adapter=adapter,
        handler=handler,
    )


def get_model(
    task_type: str
) -> ModelSpec | None:
    return MODEL_REGISTRY.get(task_type)


# -------------------------------------------------
# Mock model handlers
# -------------------------------------------------

from app.services.mock_models import (
    mock_vqa_handler,
    mock_caption_handler,
    mock_grounding_handler,
    mock_change_handler,
    mock_optical_sar_handler,
)


# -------------------------------------------------
# Register SatQuery specialist models
# -------------------------------------------------

register_model(
    name="SatQuery RS-VLM",
    task_type="vqa",
    version="0.1.0",
    description=(
        "Remote-sensing visual question answering model."
    ),
    handler=mock_vqa_handler,
)


register_model(
    name="SatQuery Captioner",
    task_type="caption",
    version="0.1.0",
    description=(
        "Remote-sensing scene captioning model."
    ),
    handler=mock_caption_handler,
)


register_model(
    name="SatQuery Grounding",
    task_type="grounding",
    version="0.1.0",
    description=(
        "Remote-sensing visual grounding model."
    ),
    handler=mock_grounding_handler,
)


register_model(
    name="SatQuery Change Model",
    task_type="change_analysis",
    version="0.1.0",
    description=(
        "Bi-temporal remote-sensing change analysis model."
    ),
    handler=mock_change_handler,
)


register_model(
    name="SatQuery Optical-SAR Fusion",
    task_type="optical_sar_fusion",
    version="0.1.0",
    description=(
        "Cross-modal optical and SAR analysis model."
    ),
    handler=mock_optical_sar_handler,
)