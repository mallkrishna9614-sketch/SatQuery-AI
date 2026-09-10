from app.services.conflict_engine import detect_conflicts
from app.services.execution_engine import execute_plan
from app.services.evidence_engine import (
    collect_evidence,
    build_model_results,
)
from app.services.confidence_engine import (
    calculate_confidence,
    confidence_label,
)
from app.services.execution_trace import build_execution_trace


def run_investigation(tasks):
    # 1. Execute specialist models
    execution_results = execute_plan(tasks)

    # 2. Collect traceable evidence
    evidence = collect_evidence(execution_results)

    # 3. Convert raw execution results into standard model results
    model_results = build_model_results(execution_results)

    # 3.5 Detect disagreements between specialist models 
    conflicts = detect_conflicts(execution_results)
    # 4. Calculate final confidence
    confidence_results = []

    for result in execution_results:
        if not result.get("success"):
            continue

        raw_result = result.get("result") or {}
        model_confidence = raw_result.get("confidence")

        if model_confidence is None:
            continue

        confidence = calculate_confidence(
            model_confidence=model_confidence
        )

        confidence_results.append({
            "task_id": result["task_id"],
            "task_type": result["task_type"],
            "model": result["model"],
            "confidence": confidence,
            "label": confidence_label(confidence),
        })

    # 5. Build observable execution trace
    trace = build_execution_trace(
        tasks=tasks,
        execution_results=execution_results,
    )

    return {
    "execution_results": execution_results,
    "model_results": model_results,
    "evidence": evidence,
    "confidence": confidence_results,
    "conflicts": conflicts,
    "trace": trace,
}
