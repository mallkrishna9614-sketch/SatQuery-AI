from app.schemas.model import EvidenceItem, ModelResult


def collect_evidence(results: list[dict]) -> list[EvidenceItem]:
    evidence = []

    for result in results:
        if not result.get("success"):
            continue

        model_result = result.get("result")

        if not model_result:
            continue

        raw_evidence = model_result.get("evidence", [])

        for item in raw_evidence:
            try:
                evidence.append(
                    EvidenceItem(
                        type=item["type"],
                        description=item["description"],
                        source=result["model"]["name"],
                        metadata={
                            "task_id": result["task_id"],
                            "task_type": result["task_type"],
                            "model_version": result["model"]["version"],
                        },
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue

    return evidence


def build_model_results(results: list[dict]) -> list[ModelResult]:
    model_results = []

    for result in results:
        model_data = result.get("model") or {}

        raw_result = result.get("result") or {}

        model_results.append(
            ModelResult(
                success=result.get("success", False),
                task_id=result["task_id"],
                task_type=result["task_type"],
                model_name=model_data.get("name", "unknown"),
                model_version=model_data.get("version", "unknown"),
                result=raw_result if result.get("success") else None,
                confidence=raw_result.get("confidence")
                if result.get("success")
                else None,
                evidence=[],
                error=result.get("error"),
            )
        )

    return model_results