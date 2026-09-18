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
from app.services.compatibility import check_compatibility



def build_finding(change_analysis: dict | None, query: str) -> dict | None:
    """Create a concise, UI-safe finding from specialist output."""
    if not change_analysis:
        return None

    changed_area = change_analysis.get("changed_area")
    regions = change_analysis.get("regions")
    comparison = change_analysis.get("comparison")

    parts = []
    if comparison:
        parts.append(f"Comparison: {comparison}.")
    if isinstance(regions, (int, float)):
        count = int(regions) if float(regions).is_integer() else regions
        parts.append(f"{count} candidate changed regions identified.")
    if isinstance(changed_area, (int, float)):
        parts.append(f"Reported changed area: {changed_area:.2f}%.")

    if "built-up" in query.lower() or "built up" in query.lower():
        summary = "Possible built-up development signal detected in the remote change analysis."
        change_type = "Possible built-up development"
    else:
        summary = "Visual change signal detected by the remote change-analysis model."
        change_type = "Visual change"

    if parts:
        summary += " " + " ".join(parts)

    return {
        "summary": summary,
        "task_type": "change_analysis",
        "change_detected": bool(
            (isinstance(regions, (int, float)) and regions > 0)
            or (isinstance(changed_area, (int, float)) and changed_area > 0)
        ),
        "change_type": change_type,
    }

def run_investigation(tasks):

    # -------------------------------------------------
    # 1. Validate raster compatibility for paired tasks
    # -------------------------------------------------

    compatibility_errors = []

    for task in tasks:

        if task.task_type == "change_analysis":

            # The remote ML change model uses one uploaded image and
            # internally handles the compare_year/current_year observations.
            # Keep pairwise raster compatibility checks only for the legacy
            # two-image temporal workflow.
            if len(task.image_ids) == 1:
                result = {"compatible": True, "reasons": []}
            else:
                result = check_compatibility(
                    image_ids=task.image_ids,
                    check_type="temporal"
                )

            if not result["compatible"]:
                compatibility_errors.extend(
                    result["reasons"]
                )

        elif task.task_type == "optical_sar_fusion":

            result = check_compatibility(
                image_ids=task.image_ids,
                check_type="optical_sar"
            )

            if not result["compatible"]:
                compatibility_errors.extend(
                    result["reasons"]
                )

    # -------------------------------------------------
    # 2. Stop before model execution if incompatible
    # -------------------------------------------------

    if compatibility_errors:

        execution_results = []

        for task in tasks:

            execution_results.append({
                "success": False,
                "task_id": task.task_id,
                "task_type": task.task_type,
                "model": None,
                "result": None,
                "error": "; ".join(
                    compatibility_errors
                )
            })

        evidence = []

        model_results = build_model_results(
            execution_results
        )

        conflicts = []

        confidence_results = []

        compatibility = {
            "compatible": False,
            "reasons": compatibility_errors,
        }

        trace = build_execution_trace(
            tasks=tasks,
            execution_results=execution_results,
            compatibility=compatibility,
            conflicts=conflicts,
        )

        return {
            "execution_results": execution_results,
            "model_results": model_results,
            "evidence": evidence,
            "confidence": confidence_results,
            "conflicts": conflicts,
            "trace": trace,
            "compatibility": compatibility,
            "change_analysis": None,
            "finding": None,
        }

    # -------------------------------------------------
    # 3. Execute specialist models
    # -------------------------------------------------

    execution_results = execute_plan(tasks)

    # -------------------------------------------------
    # 4. Collect traceable evidence
    # -------------------------------------------------

    evidence = collect_evidence(
        execution_results
    )

    # -------------------------------------------------
    # 5. Standardize model results
    # -------------------------------------------------

    model_results = build_model_results(
        execution_results
    )

    # -------------------------------------------------
    # 6. Detect model disagreements
    # -------------------------------------------------

    conflicts = detect_conflicts(
        execution_results
    )

    # -------------------------------------------------
    # 7. Calculate confidence
    # -------------------------------------------------

    confidence_results = []

    for result in execution_results:

        if not result.get("success"):
            continue

        raw_result = (
            result.get("result")
            or {}
        )

        model_confidence = raw_result.get(
            "confidence"
        )

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
            "label": confidence_label(
                confidence
            ),
        })

    # -------------------------------------------------
    # 8. Build compatibility information
    # -------------------------------------------------

    compatibility = {
        "compatible": True,
        "reasons": [],
    }

    # -------------------------------------------------
    # 9. Build observable execution trace
    # -------------------------------------------------

    trace = build_execution_trace(
        tasks=tasks,
        execution_results=execution_results,
        compatibility=compatibility,
        conflicts=conflicts,
    )

    # -------------------------------------------------
    # 10. Normalize remote change-analysis metadata
    # -------------------------------------------------

    change_analysis = None

    for result in execution_results:
        if result.get("success") and result.get("task_type") == "change_analysis":
            raw = result.get("result") or {}
            change_analysis = {
                "comparison": raw.get("comparison"),
                "reference_image": raw.get("reference_image") or raw.get("reference"),
                "match_score": raw.get("match_score"),
                "changed_area": raw.get("changed_area"),
                "regions": raw.get("regions"),
                "signal": raw.get("signal"),
                "reproduction_id": raw.get("reproduction_id"),
            }
            change_analysis = {
                key: value for key, value in change_analysis.items()
                if value is not None
            }
            break

    finding = build_finding(
        change_analysis=change_analysis,
        query=next(
            (task.query or "" for task in tasks if task.task_type == "change_analysis"),
            "",
        ),
    )

    # -------------------------------------------------
    # 11. Return complete investigation
    # -------------------------------------------------

    return {
        "execution_results": execution_results,
        "model_results": model_results,
        "evidence": evidence,
        "confidence": confidence_results,
        "conflicts": conflicts,
        "trace": trace,
        "compatibility": compatibility,
        "change_analysis": change_analysis,
        "finding": finding,
    }