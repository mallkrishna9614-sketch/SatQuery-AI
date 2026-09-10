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

    # -------------------------------------------------
    # Detect investigation capabilities
    # -------------------------------------------------

    is_temporal = (
        len(image_ids) == 2
        and any(
            keyword in query_lower
            for keyword in [
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
                "new construction",
            ]
        )
    )

    is_multimodal = (
        len(image_ids) == 2
        and any(
            keyword in query_lower
            for keyword in [
                "sar",
                "radar",
                "optical and sar",
                "optical + sar",
                "multimodal",
                "cross-modal",
            ]
        )
    )

    is_grounding = any(
        keyword in query_lower
        for keyword in [
            "where",
            "locate",
            "find",
            "region",
            "area",
            "location",
            "identify where",
        ]
    )

    # -------------------------------------------------
    # Multi-step temporal investigation
    # -------------------------------------------------

    if is_temporal:

        tasks = [
            create_task(
                task_type="change_analysis",
                image_ids=image_ids,
                query=query,
            )
        ]

        # If the user asks where the change occurred,
        # follow change detection with grounding.
        if is_grounding:

            tasks.append(
                create_task(
                    task_type="grounding",
                    image_ids=image_ids,
                    query=query,
                    parameters={
                        "depends_on": tasks[0].task_id,
                        "purpose": "locate_detected_change",
                    },
                )
            )

        return tasks

    # -------------------------------------------------
    # Multi-step optical + SAR investigation
    # -------------------------------------------------

    if is_multimodal:

        tasks = [
            create_task(
                task_type="optical_sar_fusion",
                image_ids=image_ids,
                query=query,
            )
        ]

        # If the user asks where the relevant feature
        # is located, add a grounding step.
        if is_grounding:

            tasks.append(
                create_task(
                    task_type="grounding",
                    image_ids=image_ids,
                    query=query,
                    parameters={
                        "depends_on": tasks[0].task_id,
                        "purpose": "locate_cross_modal_feature",
                    },
                )
            )

        return tasks

    # -------------------------------------------------
    # Single-image grounding
    # -------------------------------------------------

    if is_grounding:

        return [
            create_task(
                task_type="grounding",
                image_ids=image_ids,
                query=query,
            )
        ]

    # -------------------------------------------------
    # Default: single-image VQA
    # -------------------------------------------------

    return [
        create_task(
            task_type="vqa",
            image_ids=image_ids,
            query=query,
        )
    ]