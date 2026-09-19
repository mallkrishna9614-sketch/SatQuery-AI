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



from app.services.image_registry import get_image


def normalize_change_regions(raw_regions, image_id: str | None = None) -> list[dict]:
    """Normalize remote ML region boxes to UI coordinates [ymin,xmin,ymax,xmax]."""
    if not isinstance(raw_regions, list):
        return []

    width = height = 1024
    if image_id:
        try:
            image = get_image(image_id) or {}
            width = int(image.get("width") or width)
            height = int(image.get("height") or height)
        except Exception:
            pass

    normalized = []
    for index, region in enumerate(raw_regions):
        if isinstance(region, dict):
            bbox = region.get("bbox") or region.get("bounding_box") or region.get("box") or region.get("coordinates")
            label = region.get("label") or region.get("class") or region.get("name") or f"Changed region {index + 1}"
            confidence = region.get("confidence")
        else:
            bbox = region
            label = f"Changed region {index + 1}"
            confidence = None

        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            continue
        try:
            a, b, c, d = [float(value) for value in bbox]
        except (TypeError, ValueError):
            continue

        scale = max(abs(a), abs(b), abs(c), abs(d))
        if scale <= 1.0:
            x1, y1, x2, y2 = a, b, c, d
        else:
            x1, y1, x2, y2 = a / width, b / height, c / width, d / height

        if x2 <= x1 or y2 <= y1:
            # Also tolerate x,y,width,height style boxes.
            if scale > 1.0:
                x2 = x1 + c / width
                y2 = y1 + d / height
            else:
                x2 = x1 + c
                y2 = y1 + d

        x1, x2 = max(0.0, min(1.0, x1)), max(0.0, min(1.0, x2))
        y1, y2 = max(0.0, min(1.0, y1)), max(0.0, min(1.0, y2))
        if x2 <= x1 or y2 <= y1:
            continue

        item = {
            "id": str(region.get("id", index + 1)) if isinstance(region, dict) else str(index + 1),
            "label": str(label),
            "bbox": [y1, x1, y2, x2],
        }
        if isinstance(confidence, (int, float)):
            item["confidence"] = float(confidence)
        normalized.append(item)

    return normalized


def build_finding(change_analysis: dict | None, query: str, image_id: str | None = None) -> dict | None:
    """Create a concise, UI-safe finding from specialist output."""
    if not change_analysis:
        return None

    changed_area = change_analysis.get("changed_area")
    raw_regions = change_analysis.get("regions")
    region_boxes = normalize_change_regions(raw_regions, image_id=image_id)
    region_count = len(raw_regions) if isinstance(raw_regions, list) else raw_regions
    comparison = change_analysis.get("comparison")

    parts = []
    if comparison:
        parts.append(f"Comparison: {comparison}.")
    if isinstance(region_count, (int, float)):
        count = int(region_count) if float(region_count).is_integer() else region_count
        parts.append(f"{count} candidate changed regions identified.")
    elif region_boxes:
        parts.append(f"{len(region_boxes)} candidate changed regions identified.")
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
            (isinstance(region_count, (int, float)) and region_count > 0)
            or bool(region_boxes)
            or (isinstance(changed_area, (int, float)) and changed_area > 0)
        ),
        "change_type": change_type,
        "regions": region_boxes,
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
                # Preserve the specialist's actual change-analysis output so
                # the frontend can render semantic region findings, overlays,
                # evidence and explanations instead of only generic metadata.
                "comparison": raw.get("comparison"),
                "reference_image": raw.get("reference_image") or raw.get("reference"),
                "match_score": raw.get("match_score"),
                "changed_area": (
                    raw.get("changed_area")
                    if raw.get("changed_area") is not None
                    else raw.get("changed_area_percent")
                ),
                "regions": raw.get("regions") or raw.get("changed_regions") or raw.get("detections"),
                "signal": raw.get("signal"),
                "reproduction_id": raw.get("reproduction_id"),
                "change_detected": raw.get("change_detected"),
                "change_type": raw.get("change_type"),
                "what_changed": (
                    raw.get("what_changed")
                    or raw.get("change_summary")
                    or raw.get("summary")
                    or raw.get("answer")
                    or raw.get("description")
                ),
                "why": (
                    raw.get("why")
                    or raw.get("explanation")
                    or raw.get("reason")
                    or raw.get("analysis")
                    or raw.get("rationale")
                ),
                "region_findings": (
                    raw.get("region_findings")
                    or raw.get("region_analysis")
                    or raw.get("semantic_findings")
                    or raw.get("change_findings")
                    or raw.get("findings")
                    or raw.get("descriptions")
                ),
                "evidence": raw.get("evidence"),
                # Preserve model-generated visual artifacts. The remote ML
                # service may return a URL, data URI, or a nested artifact
                # object; do not discard it before the frontend receives it.
                "change_visualization_url": (
                    raw.get("change_visualization_url")
                    or raw.get("change_visualization")
                    or raw.get("annotated_image")
                    or raw.get("overlay_image")
                    or raw.get("current_with_changes")
                    or raw.get("visualization_url")
                ),
                "change_mask_url": (
                    raw.get("change_mask_url")
                    or raw.get("change_mask")
                    or raw.get("change_map")
                    or raw.get("mask_url")
                ),
                "sar_mask_url": (
                    raw.get("sar_mask_url")
                    or raw.get("sar_change_mask")
                    or raw.get("sar_mask")
                ),
                "visualization": raw.get("visualization"),
                "artifacts": raw.get("artifacts"),
            }
            change_analysis = {
                key: value for key, value in change_analysis.items()
                if value is not None
            }
            break

    change_task = next((task for task in tasks if task.task_type == "change_analysis"), None)
    finding = build_finding(
        change_analysis=change_analysis,
        query=change_task.query if change_task else "",
        image_id=change_task.image_ids[0] if change_task and change_task.image_ids else None,
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