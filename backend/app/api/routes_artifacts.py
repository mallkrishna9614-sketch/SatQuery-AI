from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from app.core.config import settings


router = APIRouter(prefix="/ml-artifacts", tags=["ml-artifacts"])


def _allowed_ml_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False

    allowed = []
    for raw in (
        settings.ML_BASE_URL,
        settings.ML_FALLBACK_BASE_URL,
    ):
        raw = raw.strip().rstrip("/")
        if raw:
            host = urlparse(raw).hostname
            if host:
                allowed.append(host)

    return parsed.hostname in set(allowed)


@router.get("/proxy")
def proxy_ml_artifact(url: str = Query(..., min_length=1)):
    """
    Proxy a visual artifact from the configured ML service.

    The browser should use this endpoint instead of directly loading a
    provider artifact URL. Only hosts configured as ML endpoints are allowed.
    """
    if not _allowed_ml_url(url):
        raise HTTPException(status_code=400, detail="Artifact URL is not an allowed ML service URL.")

    try:
        with httpx.Client(
            timeout=httpx.Timeout(settings.ML_TIMEOUT_SECONDS)
        ) as client:
            upstream = client.get(
                url,
                headers={"Accept": "image/*,application/json;q=0.9,*/*;q=0.8"},
                follow_redirects=True,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach ML artifact: {exc}") from exc

    if upstream.status_code >= 400:
        raise HTTPException(
            status_code=upstream.status_code,
            detail=f"ML artifact returned HTTP {upstream.status_code}.",
        )

    content_type = upstream.headers.get("content-type", "application/octet-stream")
    return Response(
        content=upstream.content,
        media_type=content_type.split(";")[0],
        headers={"Cache-Control": "public, max-age=300"},
    )
