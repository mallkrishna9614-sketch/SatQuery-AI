import uuid

from app.schemas.investigation import (
    InvestigationTask,
    TaskType
)


def create_task(
    task_type: TaskType,
    image_ids: list[str],
    query: str,
    parameters: dict | None = None
):
    return InvestigationTask(
        task_id="task_" + uuid.uuid4().hex[:8],
        task_type=task_type,
        image_ids=image_ids,
        query=query,
        parameters=parameters or {}
    )


def build_investigation_plan(
    query: str,
    image_ids: list[str]
):
    query_lower = query.lower()

    tasks = []

    # -----------------------------
    # Change analysis
    # -----------------------------

    if any(
        word in query_lower
        for word in [
            "change",
            "changed",
            "before and after",
            "temporal",
            "growth",
            "new construction"
        ]
    ):

        tasks.append(
            create_task(
                task_type="change_analysis",
                image_ids=image_ids,
                query=query
            )
        )

    # -----------------------------
    # Optical + SAR
    # -----------------------------

    elif any(
        word in query_lower
        for word in [
            "sar",
            "radar",
            "optical and sar",
            "multimodal"
        ]
    ):

        tasks.append(
            create_task(
                task_type="optical_sar_fusion",
                image_ids=image_ids,
                query=query
            )
        )

    # -----------------------------
    # Grounding
    # -----------------------------

    elif any(
        word in query_lower
        for word in [
            "where",
            "locate",
            "find",
            "region",
            "area"
        ]
    ):

        tasks.append(
            create_task(
                task_type="grounding",
                image_ids=image_ids,
                query=query
            )
        )

    # -----------------------------
    # Default VQA
    # -----------------------------

    else:

        tasks.append(
            create_task(
                task_type="vqa",
                image_ids=image_ids,
                query=query
            )
        )

    return tasks