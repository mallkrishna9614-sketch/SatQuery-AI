import uuid

from app.schemas.investigation import (
    InvestigationTask,
    TaskType,
)


def create_task(
    task_type: TaskType,
    image_ids: list[str],
    query: str,
    parameters: dict | None = None,
):
    return InvestigationTask(
        task_id="task_" + uuid.uuid4().hex[:8],
        task_type=task_type,
        image_ids=image_ids,
        query=query,
        parameters=parameters or {},
    )


def build_investigation_plan(
    query: str,
    image_ids: list[str],
):
    query_lower = query.lower()

    # --------------------------------------------------
    # 1. True temporal/change analysis
    # --------------------------------------------------

    temporal_keywords = [
    "before and after",
    "between the two images",
    "compare the two images",
    "compare these two images",
    "compare these images",
    "temporal change",
    "over time",
    "changed between",
    "change between",
    "new construction between",
    ]

    if (
        len(image_ids) == 2
        and any(
            keyword in query_lower
            for keyword in temporal_keywords
        )
    ):
        return [
            create_task(
                task_type="change_analysis",
                image_ids=image_ids,
                query=query,
            )
        ]

    # --------------------------------------------------
    # 2. Optical + SAR analysis
    # --------------------------------------------------

    multimodal_keywords = [
        "sar",
        "radar",
        "optical and sar",
        "optical + sar",
        "multimodal",
        "cross-modal",
    ]

    if (
        len(image_ids) == 2
        and any(
            keyword in query_lower
            for keyword in multimodal_keywords
        )
    ):
        return [
            create_task(
                task_type="optical_sar_fusion",
                image_ids=image_ids,
                query=query,
            )
        ]

    # --------------------------------------------------
    # 3. Single-image spatial/region request
    # --------------------------------------------------

    grounding_keywords = [
        "where",
        "locate",
        "find",
        "region",
        "area",
        "location",
        "identify where",
    ]

    if any(
        keyword in query_lower
        for keyword in grounding_keywords
    ):
        return [
            create_task(
                task_type="grounding",
                image_ids=image_ids,
                query=query,
            )
        ]

    # --------------------------------------------------
    # 4. Default single-image VQA
    # --------------------------------------------------

    return [
        create_task(
            task_type="vqa",
            image_ids=image_ids,
            query=query,
        )
    ]