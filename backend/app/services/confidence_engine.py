def calculate_confidence(
    model_confidence: float,
    temporal_consistency: float = 1.0,
    spatial_consistency: float = 1.0,
    cross_modal_agreement: float = 1.0,
    evidence_quality: float = 1.0,
) -> float:

    weights = {
        "model": 0.40,
        "temporal": 0.15,
        "spatial": 0.15,
        "cross_modal": 0.15,
        "evidence": 0.15,
    }

    confidence = (
        model_confidence * weights["model"]
        + temporal_consistency * weights["temporal"]
        + spatial_consistency * weights["spatial"]
        + cross_modal_agreement * weights["cross_modal"]
        + evidence_quality * weights["evidence"]
    )

    return round(max(0.0, min(1.0, confidence)), 4)


def confidence_label(confidence: float) -> str:
    if confidence >= 0.80:
        return "high"

    if confidence >= 0.60:
        return "medium"

    return "low"