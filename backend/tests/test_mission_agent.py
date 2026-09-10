from app.services.mission_agent import build_investigation_plan


def test_single_image_vqa():
    tasks = build_investigation_plan(
        "What is visible in this image?",
        ["img_test"]
    )

    assert len(tasks) == 1
    assert tasks[0].task_type == "vqa"


def test_single_image_grounding():
    tasks = build_investigation_plan(
        "Where are the buildings in this image?",
        ["img_test"]
    )

    assert len(tasks) == 1
    assert tasks[0].task_type == "grounding"


def test_temporal_change():
    tasks = build_investigation_plan(
        "Compare these two images for new construction.",
        ["img_before", "img_after"]
    )

    assert len(tasks) == 1
    assert tasks[0].task_type == "change_analysis"


def test_optical_sar_fusion():
    tasks = build_investigation_plan(
        "Analyze the optical and SAR imagery together.",
        ["img_optical", "img_sar"]
    )

    assert len(tasks) == 1
    assert tasks[0].task_type == "optical_sar_fusion"