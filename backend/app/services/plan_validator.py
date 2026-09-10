from app.schemas.investigation import InvestigationTask


def validate_task(
    task: InvestigationTask
):
    errors = []

    # -----------------------------
    # VQA / Caption / Grounding
    # -----------------------------

    if task.task_type in {
        "vqa",
        "caption",
        "grounding"
    }:

        if len(task.image_ids) < 1:
            errors.append(
                f"{task.task_type} requires at least one image."
            )

    # -----------------------------
    # Change Analysis
    # -----------------------------

    elif task.task_type == "change_analysis":

        if len(task.image_ids) != 2:
            errors.append(
                "Change analysis requires exactly two "
                "temporal images."
            )

    # -----------------------------
    # Optical + SAR Fusion
    # -----------------------------

    elif task.task_type == "optical_sar_fusion":

        if len(task.image_ids) != 2:
            errors.append(
                "Optical-SAR fusion requires exactly "
                "two images."
            )

    return errors


def validate_plan(
    tasks: list[InvestigationTask]
):
    errors = []

    for task in tasks:

        task_errors = validate_task(task)

        errors.extend(task_errors)

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }