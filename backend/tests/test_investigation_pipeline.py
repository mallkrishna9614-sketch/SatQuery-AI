from app.services.investigation_pipeline import run_investigation
from app.services.mission_agent import build_investigation_plan


def test_full_vqa_pipeline():

    tasks = build_investigation_plan(
        "What is visible in this image?",
        ["img_test"]
    )

    result = run_investigation(tasks)

    assert len(result["model_results"]) == 1
    assert len(result["evidence"]) >= 1
    assert len(result["confidence"]) == 1
    assert result["conflicts"] == []
    assert len(result["trace"]) >= 1


def test_full_temporal_pipeline():

    tasks = build_investigation_plan(
        "Compare these two images for new construction.",
        ["img_before", "img_after"]
    )

    result = run_investigation(tasks)

    assert len(result["model_results"]) == 1
    assert result["model_results"][0].task_type == "change_analysis"
    assert len(result["evidence"]) >= 1
    assert len(result["confidence"]) == 1
    assert len(result["trace"]) >= 1