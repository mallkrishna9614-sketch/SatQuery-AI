from app.schemas.investigation import InvestigationTask
from app.services.model_registry import get_model


def execute_task(
    task: InvestigationTask
):
    # -----------------------------
    # 1. Find registered model
    # -----------------------------

    model = get_model(
        task.task_type
    )

    if model is None:
        return {
            "success": False,
            "task_id": task.task_id,
            "task_type": task.task_type,
            "model": None,
            "result": None,
            "error": (
                f"No model registered for "
                f"task type: {task.task_type}"
            )
        }

    # -----------------------------
    # 2. Check model handler
    # -----------------------------

    if model.handler is None:
        return {
            "success": False,
            "task_id": task.task_id,
            "task_type": task.task_type,
            "model": {
                "name": model.name,
                "version": model.version
            },
            "result": None,
            "error": (
                f"Model '{model.name}' is registered "
                f"but its handler is not connected yet."
            )
        }

    # -----------------------------
    # 3. Execute model
    # -----------------------------

    try:

        result = model.handler(
            task
        )

        return {
            "success": True,
            "task_id": task.task_id,
            "task_type": task.task_type,
            "model": {
                "name": model.name,
                "version": model.version
            },
            "result": result,
            "error": None
        }

    except Exception as exc:

        return {
            "success": False,
            "task_id": task.task_id,
            "task_type": task.task_type,
            "model": {
                "name": model.name,
                "version": model.version
            },
            "result": None,
            "error": str(exc)
        }


def execute_plan(
    tasks: list[InvestigationTask]
):
    results = []

    for task in tasks:

        result = execute_task(
            task
        )

        results.append(
            result
        )

    return results