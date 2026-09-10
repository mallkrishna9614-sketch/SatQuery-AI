from fastapi.testclient import TestClient

from app.main import app
from app.services import execution_engine
from app.services import investigation_pipeline


client = TestClient(app)


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


def test_investigation_api_end_to_end(monkeypatch):

    # Avoid requiring real images in the database
    monkeypatch.setattr(
        execution_engine,
        "get_image_paths",
        fake_image_paths
    )

    # Avoid real raster compatibility checks
    monkeypatch.setattr(
        investigation_pipeline,
        "check_compatibility",
        fake_compatibility
    )

    # ---------------------------------------------
    # 1. Create investigation
    # ---------------------------------------------

    response = client.post(
        "/api/v1/investigations/",
        json={
            "query": (
                "Compare these two images for "
                "new construction and tell me "
                "where it occurred."
            ),
            "image_ids": [
                "img_before",
                "img_after"
            ]
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed"

    investigation_id = data["investigation_id"]

    assert investigation_id.startswith("inv_")

    # ---------------------------------------------
    # 2. Verify multi-step plan
    # ---------------------------------------------

    assert len(data["tasks"]) == 2

    assert (
        data["tasks"][0]["task_type"]
        == "change_analysis"
    )

    assert (
        data["tasks"][1]["task_type"]
        == "grounding"
    )

    assert (
        data["tasks"][1]["parameters"]["depends_on"]
        == data["tasks"][0]["task_id"]
    )

    # ---------------------------------------------
    # 3. Verify execution
    # ---------------------------------------------

    assert len(
        data["execution"]["model_results"]
    ) == 2

    assert all(
        result["success"]
        for result in data["execution"]["model_results"]
    )

    assert len(
        data["execution"]["evidence"]
    ) >= 2

    # ---------------------------------------------
    # 4. Retrieve saved investigation
    # ---------------------------------------------

    response = client.get(
        f"/api/v1/investigations/{investigation_id}"
    )

    assert response.status_code == 200

    saved = response.json()

    assert (
        saved["investigation_id"]
        == investigation_id
    )

    assert saved["status"] == "completed"

    assert saved["execution"] is not None

    # ---------------------------------------------
    # 5. Retrieve generated report
    # ---------------------------------------------

    response = client.get(
        f"/api/v1/investigations/"
        f"{investigation_id}/report"
    )

    assert response.status_code == 200

    assert (
        response.headers["content-type"]
        .startswith("application/json")
    )

    assert len(response.content) > 0