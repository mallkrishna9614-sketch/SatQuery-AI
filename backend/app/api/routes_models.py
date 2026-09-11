from fastapi import APIRouter

from app.services.model_registry import MODEL_REGISTRY


router = APIRouter(
    prefix="/models",
    tags=["models"]
)


@router.get("/")
def list_models():

    models = []

    for model in MODEL_REGISTRY.values():

        models.append({
            "name": model.name,
            "task_type": model.task_type,
            "version": model.version,
            "description": model.description,
            "adapter_available": (
                model.adapter is not None
            ),
            "handler_available": (
                model.handler is not None
            ),
        })

    return {
        "models": models,
        "count": len(models)
    }