def calculate_confidence(
    model_confidence: float,
    temporal_consistency: float | None = None,
    spatial_consistency: float | None = None,
    cross_modal_agreement: float | None = None,
    evidence_quality: float | None = None,
) -> float:
    """
    Return the model confidence unless independent corroborating signals are
    actually supplied.

    Previously, omitted corroboration values defaulted to 1.0 and inflated a
    model score such as 0.82 to 0.928. That made the UI disagree with the
    specialist model's own confidence. We only apply the weighted evidence
    fusion when all corroborating dimensions are explicitly available.
    """
    model = max(0.0, min(1.0, float(model_confidence)))

    corroboration = (
        temporal_consistency,
        spatial_consistency,
        cross_modal_agreement,
        evidence_quality,
    )

    if any(value is None for value in corroboration):
        return round(model, 4)

    weights = {
        "model": 0.40,
        "temporal": 0.15,
        "spatial": 0.15,
        "cross_modal": 0.15,
        "evidence": 0.15,
    }

    confidence = (
        model * weights["model"]
        + float(temporal_consistency) * weights["temporal"]
        + float(spatial_consistency) * weights["spatial"]
        + float(cross_modal_agreement) * weights["cross_modal"]
        + float(evidence_quality) * weights["evidence"]
    )

    return round(max(0.0, min(1.0, confidence)), 4)


def confidence_label(confidence: float) -> str:
    if confidence >= 0.80:
        return "high"

    if confidence >= 0.60:
        return "medium"

    return "low"
