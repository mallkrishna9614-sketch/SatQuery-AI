from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_invalid_modality():

    response = client.post(
        "/api/v1/images/upload",
        files={
            "file": (
                "test.tif",
                BytesIO(b"fake raster"),
                "image/tiff",
            )
        },
        data={
            "modality": "invalid"
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_MODALITY"


def test_unsupported_format():

    response = client.post(
        "/api/v1/images/upload",
        files={
            "file": (
                "test.png",
                BytesIO(b"fake image"),
                "image/png",
            )
        },
        data={
            "modality": "optical"
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_FORMAT"


def test_missing_modality():

    response = client.post(
        "/api/v1/images/upload",
        files={
            "file": (
                "test.tif",
                BytesIO(b"fake raster"),
                "image/tiff",
            )
        },
    )

    assert response.status_code == 422