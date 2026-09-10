from app.schemas.investigation import InvestigationTask
from app.services.model_registry import get_model
from app.services.image_registry import get_image


def get_image_paths(image_ids: list[str]) -> list[str]:
    image_paths = []

    for image_id in image_ids:
        image = get_image(image_id)

        if image is None:
            raise ValueError(
                f"Image not found: {image_id}"
            )

        image_paths.append(
            image["file_path"]
        )

    return image_paths


def execute_task(
    task: InvestigationTask,
    previous_results: dict | None = None
):

    # -------------------------------------------------
    # 1. Find registered specialist model
    # -------------------------------------------------

    model = get_model(task.task_type)

    if model is None:
        return {
            "success": False,
            "task_id": task.task_id,
            "task_type": task.task_type,
            "model": None,
            "result": None,
            "error": (
                f"No model registered for task type: "
                f"{task.task_type}"
            )
        }

    # -------------------------------------------------
    # 2. Resolve actual image paths
    # -------------------------------------------------

    try:

        image_paths = get_image_paths(
            task.image_ids
        )

    except ValueError as exc:

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

    # -------------------------------------------------
    # 3. Build execution context
    # -------------------------------------------------

    execution_context = {}

    if previous_results:

        execution_context = {
            "previous_results": previous_results
        }

    # -------------------------------------------------
    # 4. Prefer real ML adapter
    # -------------------------------------------------

    if model.adapter is not None:

        try:

            result = model.adapter.predict(
                task=task,
                image_paths=image_paths
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

    # -------------------------------------------------
    # 5. Fall back to mock handler
    # -------------------------------------------------

    if model.handler is not None:

        try:

            # Current mock handlers accept only task.
            # The execution context is attached temporarily
            # through task parameters for downstream use.

            if execution_context:

                task.parameters = {
                    **task.parameters,
                    "_execution_context": execution_context
                }

            result = model.handler(task)

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

    # -------------------------------------------------
    # 6. No adapter or handler
    # -------------------------------------------------

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
            "but no adapter or handler is connected."
        )
    }


def execute_plan(
    tasks: list[InvestigationTask]
):

    results = []

    # Stores results by task_id so later tasks
    # can depend on earlier tasks.
    results_by_task_id = {}

    for task in tasks:

        # -------------------------------------------------
        # Check task dependency
        # -------------------------------------------------

        dependency_id = task.parameters.get(
            "depends_on"
        )

        previous_results = None

        if dependency_id:

            dependency_result = (
                results_by_task_id.get(
                    dependency_id
                )
            )

            if dependency_result is None:

                result = {
                    "success": False,
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "model": None,
                    "result": None,
                    "error": (
                        f"Dependency task not found: "
                        f"{dependency_id}"
                    )
                }

                results.append(result)
                results_by_task_id[
                    task.task_id
                ] = result

                continue

            # Do not execute dependent task if
            # its prerequisite failed.
            if not dependency_result["success"]:

                result = {
                    "success": False,
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "model": None,
                    "result": None,
                    "error": (
                        f"Dependency task failed: "
                        f"{dependency_id}"
                    )
                }

                results.append(result)
                results_by_task_id[
                    task.task_id
                ] = result

                continue

            previous_results = {
                dependency_id: dependency_result
            }

        # -------------------------------------------------
        # Execute task
        # -------------------------------------------------

        result = execute_task(
            task=task,
            previous_results=previous_results
        )

        results.append(result)

        results_by_task_id[
            task.task_id
        ] = result

    return results