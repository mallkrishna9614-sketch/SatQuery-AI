from dataclasses import dataclass
from typing import Callable
from app.services.mock_models import (
    mock_vqa_handler,
    mock_caption_handler,
    mock_grounding_handler,
    mock_change_handler,
    mock_optical_sar_handler,
)


@dataclass
class ModelSpec:
    name: str
    task_type: str
    version: str
    description: str
    handler: Callable | None = None


# --------------------------------
# Model Registry
# --------------------------------

MODEL_REGISTRY: dict[str, ModelSpec] = {}


# --------------------------------
# Register a model
# --------------------------------

def register_model(
    name: str,
    task_type: str,
    version: str,
    description: str,
    handler: Callable | None = None
):
    MODEL_REGISTRY[task_type] = ModelSpec(
        name=name,
        task_type=task_type,
        version=version,
        description=description,
        handler=handler
    )


# --------------------------------
# Get model for task
# --------------------------------

def get_model(
    task_type: str
) -> ModelSpec | None:

    return MODEL_REGISTRY.get(task_type)


# --------------------------------
# Register SatQuery specialists
# --------------------------------

register_model(
    name="SatQuery RS-VLM",
    task_type="vqa",
    version="0.1.0",
    description="Remote-sensing vision-language model for image question answering.",
    handler=mock_vqa_handler
)

register_model(
    name="SatQuery Captioner",
    task_type="caption",
    version="0.1.0",
    description="Remote-sensing image captioning and scene description model.",
    handler=mock_vqa_handler
)

register_model(
    name="SatQuery Grounding",
    task_type="grounding",
    version="0.1.0",
    description="Remote-sensing region grounding model.",
    handler=mock_vqa_handler
)

register_model(
    name="SatQuery Change Model",
    task_type="change_analysis",
    version="0.1.0",
    description="Bi-temporal remote-sensing change analysis model.",
    handler=mock_vqa_handler
)

register_model(
    name="SatQuery Optical-SAR Fusion",
    task_type="optical_sar_fusion",
    version="0.1.0",
    description="Co-registered optical and SAR analysis model.",
    handler=mock_vqa_handler
)