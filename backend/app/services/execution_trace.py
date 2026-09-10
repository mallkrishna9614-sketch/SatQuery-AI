from datetime import datetime, timezone


def create_trace_entry(
    step: str,
    status: str,
    details: dict | None = None
):
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "step": step,
        "status": status,
        "details": details or {}
    }


def build_execution_trace(
    tasks,
    execution_results,
    compatibility=None,
    conflicts=None
):
    trace = []

    # 1. Mission received
    trace.append(
        create_trace_entry(
            step="mission_received",
            status="completed",
            details={
                "task_count": len(tasks)
            }
        )
    )

    # 2. Plan created
    trace.append(
        create_trace_entry(
            step="plan_created",
            status="completed",
            details={
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "image_ids": task.image_ids,
                        "parameters": task.parameters
                    }
                    for task in tasks
                ]
            }
        )
    )

    # 3. Plan validation
    trace.append(
        create_trace_entry(
            step="plan_validation",
            status="completed",
            details={
                "valid": True
            }
        )
    )

    # 4. Raster compatibility
    if compatibility is not None:
        trace.append(
            create_trace_entry(
                step="raster_compatibility",
                status=(
                    "completed"
                    if compatibility.get("compatible")
                    else "failed"
                ),
                details=compatibility
            )
        )

    # 5. Dependency resolution
    dependencies = []

    for task in tasks:

        dependency_id = task.parameters.get(
            "depends_on"
        )

        if dependency_id:

            dependencies.append({
                "task_id": task.task_id,
                "depends_on": dependency_id,
                "purpose": task.parameters.get(
                    "purpose"
                )
            })

    trace.append(
        create_trace_entry(
            step="dependency_resolution",
            status="completed",
            details={
                "dependency_count": len(
                    dependencies
                ),
                "dependencies": dependencies
            }
        )
    )

    # 6. Model execution
    for result in execution_results:

        task = next(
            (
                task
                for task in tasks
                if task.task_id == result["task_id"]
            ),
            None
        )

        dependency_id = None

        if task is not None:
            dependency_id = task.parameters.get(
                "depends_on"
            )

        trace.append(
            create_trace_entry(
                step="model_execution",
                status=(
                    "completed"
                    if result["success"]
                    else "failed"
                ),
                details={
                    "task_id": result["task_id"],
                    "task_type": result["task_type"],
                    "model": result["model"],
                    "depends_on": dependency_id,
                    "error": result["error"]
                }
            )
        )

    # 7. Evidence collection
    successful_results = [
        result
        for result in execution_results
        if result["success"]
    ]

    trace.append(
        create_trace_entry(
            step="evidence_collection",
            status="completed",
            details={
                "successful_models": len(
                    successful_results
                )
            }
        )
    )

    # 8. Conflict detection
    if conflicts is not None:
        trace.append(
            create_trace_entry(
                step="conflict_detection",
                status="completed",
                details={
                    "conflict_count": len(conflicts),
                    "conflicts": conflicts
                }
            )
        )

    # 9. Confidence calculation
    trace.append(
        create_trace_entry(
            step="confidence_calculation",
            status="completed",
            details={
                "models_evaluated": len(
                    successful_results
                )
            }
        )
    )

    # 10. Investigation completed
    trace.append(
        create_trace_entry(
            step="investigation_completed",
            status="completed"
        )
    )

    return trace