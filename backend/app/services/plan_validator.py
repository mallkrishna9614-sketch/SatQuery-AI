from app.schemas.investigation import InvestigationTask


def validate_task(task: InvestigationTask):
    errors = []

    if task.task_type in {
        "vqa",
        "caption",
        "grounding"
    }:
        if len(task.image_ids) < 1:
            errors.append(
                f"{task.task_type} requires at least one image."
            )

    elif task.task_type == "change_analysis":

        remote_ml_temporal = bool(
            (task.parameters or {}).get("remote_ml_temporal")
        )

        if remote_ml_temporal:
            if len(task.image_ids) != 1:
                errors.append(
                    "Remote ML temporal analysis requires exactly one image."
                )
        elif len(task.image_ids) != 2:
            errors.append(
                "Change analysis requires exactly two temporal images."
            )

    elif task.task_type == "optical_sar_fusion":

        if len(task.image_ids) != 2:
            errors.append(
                "Optical-SAR fusion requires exactly two images."
            )

    return errors


def validate_plan(tasks: list[InvestigationTask]):

    errors = []

    for task in tasks:
        errors.extend(
            validate_task(task)
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }