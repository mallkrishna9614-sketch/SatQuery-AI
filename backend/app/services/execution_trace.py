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


def build_execution_trace(tasks, execution_results):
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

    # 2. Investigation plan created
    trace.append(
        create_trace_entry(
            step="plan_created",
            status="completed",
            details={
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "image_ids": task.image_ids
                    }
                    for task in tasks
                ]
            }
        )
    )

    # 3. Plan validated
    trace.append(
        create_trace_entry(
            step="plan_validation",
            status="completed",
            details={
                "valid": True
            }
        )
    )

    # 4. Specialist model execution
    for result in execution_results:
        trace.append(
            create_trace_entry(
                step="model_execution",
                status="completed"
                if result["success"]
                else "failed",
                details={
                    "task_id": result["task_id"],
                    "task_type": result["task_type"],
                    "model": result["model"],
                    "error": result["error"]
                }
            )
        )

    # 5. Evidence collection
    successful_results = [
        result for result in execution_results
        if result["success"]
    ]

    trace.append(
        create_trace_entry(
            step="evidence_collection",
            status="completed",
            details={
                "successful_models": len(successful_results)
            }
        )
    )

    # 6. Confidence calculation
    trace.append(
        create_trace_entry(
            step="confidence_calculation",
            status="completed",
            details={
                "models_evaluated": len(successful_results)
            }
        )
    )

    # 7. Investigation completed
    trace.append(
        create_trace_entry(
            step="investigation_completed",
            status="completed"
        )
    )

    return trace