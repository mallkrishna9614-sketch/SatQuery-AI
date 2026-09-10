from app.services.investigation_pipeline import run_investigation
from app.services.mission_agent import build_investigation_plan


def fake_image_paths(image_ids):
    return [
        f"data/uploads/{image_id}.tif"
        for image_id in image_ids
    ]


def fake_compatibility(
    image_ids,
    check_type
):
    return {
        "compatible": True,
        "reasons": [],
        "images": []
    }


def test_full_vqa_pipeline(monkeypatch):

    import app.services.execution_engine as execution_engine

    monkeypatch.setattr(
        execution_engine,
        "get_image_paths",
        fake_image_paths
    )

    tasks = build_investigation_plan(
        "What is visible in this image?",
        ["img_test"]
    )

    result = run_investigation(tasks)

    assert len(result["model_results"]) == 1
    assert result["model_results"][0].success is True
    assert len(result["evidence"]) >= 1
    assert len(result["confidence"]) == 1
    assert result["conflicts"] == []
    assert len(result["trace"]) >= 1


def test_full_temporal_pipeline(monkeypatch):

    import app.services.execution_engine as execution_engine
    import app.services.investigation_pipeline as pipeline

    monkeypatch.setattr(
        execution_engine,
        "get_image_paths",
        fake_image_paths
    )

    monkeypatch.setattr(
        pipeline,
        "check_compatibility",
        fake_compatibility
    )

    tasks = build_investigation_plan(
        "Compare these two images for new construction.",
        ["img_before", "img_after"]
    )

    result = run_investigation(tasks)

    assert len(result["model_results"]) == 1
    assert result["model_results"][0].success is True
    assert result["model_results"][0].task_type == "change_analysis"
    assert len(result["evidence"]) >= 1
    assert len(result["confidence"]) == 1
    assert result["conflicts"] == []
    assert result["compatibility"]["compatible"] is True
    assert len(result["trace"]) >= 1
def test_multi_step_dependency_pipeline(monkeypatch):

    import app.services.execution_engine as execution_engine
    import app.services.investigation_pipeline as pipeline

    monkeypatch.setattr(
        execution_engine,
        "get_image_paths",
        fake_image_paths
    )

    monkeypatch.setattr(
        pipeline,
        "check_compatibility",
        fake_compatibility
    )

    tasks = build_investigation_plan(
        "Compare these two images for new construction and tell me where it occurred.",
        ["img_before", "img_after"]
    )

    # The Mission Agent should create:
    # 1. change_analysis
    # 2. grounding depending on change_analysis
    assert len(tasks) == 2

    assert tasks[0].task_type == "change_analysis"
    assert tasks[1].task_type == "grounding"

    assert tasks[1].parameters["depends_on"] == (
        tasks[0].task_id
    )

    result = run_investigation(tasks)

    # Both tasks should execute successfully
    assert len(result["model_results"]) == 2

    assert result["model_results"][0].success is True
    assert result["model_results"][1].success is True

    # Verify execution order
    assert (
        result["model_results"][0].task_type
        == "change_analysis"
    )

    assert (
        result["model_results"][1].task_type
        == "grounding"
    )

    # Evidence should come from both tasks
    assert len(result["evidence"]) >= 2

    # Both tasks should have confidence results
    assert len(result["confidence"]) == 2

    # No conflicts in the mock pipeline
    assert result["conflicts"] == []

    # Dependency should appear in the execution trace
    dependency_steps = [
        step
        for step in result["trace"]
        if step["step"] == "dependency_resolution"
    ]

    assert len(dependency_steps) == 1

    assert (
        dependency_steps[0]["details"]["dependency_count"]
        == 1
    )