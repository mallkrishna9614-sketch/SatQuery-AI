import base64
import time
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.investigation import InvestigationTask
from app.services.model_adapter import ModelAdapter


class RemoteMLAdapter(ModelAdapter):
    """
    Adapter for the remote SatQuery ML inference service.

    Current integration targets the ML team's asynchronous change-analysis API:
      POST /api/start
      GET  /api/status/{job_id}

    The remote service is intentionally kept behind this adapter so the
    investigation engine and frontend do not depend on ML-provider details.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        poll_interval_seconds: float | None = None,
    ):
        configured_base = (
            base_url or settings.ML_BASE_URL
        ).strip().rstrip("/")
        fallback_base = settings.ML_FALLBACK_BASE_URL.strip().rstrip("/")

        self.base_url = configured_base or fallback_base
        self.fallback_base_url = (
            fallback_base
            if fallback_base and fallback_base != self.base_url
            else None
        )
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.ML_TIMEOUT_SECONDS
        )
        self.poll_interval_seconds = (
            poll_interval_seconds
            if poll_interval_seconds is not None
            else settings.ML_POLL_INTERVAL_SECONDS
        )

    @staticmethod
    def _encode_image(path: str) -> str:
        with open(path, "rb") as image_file:
            return base64.b64encode(
                image_file.read()
            ).decode("utf-8")

    @staticmethod
    def _extract_status_payload(payload: Any) -> tuple[str | None, dict]:
        if not isinstance(payload, dict):
            return None, {"raw_response": payload}

        status = payload.get("status")

        # Common API shapes:
        # {"status": "...", "result": {...}}
        # {"job": {"status": "...", "result": {...}}}
        # {"data": {"status": "...", "result": {...}}}
        for key in ("job", "data", "result"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                if status is None:
                    status = nested.get("status")
                if "result" in nested:
                    return status, nested["result"]

        return status, payload


    @staticmethod
    def _artifact_url(value: Any, base_url: str) -> Any:
        """Resolve ML-provider relative artifact paths to browser-loadable URLs."""
        if not isinstance(value, str):
            return value
        value = value.strip()
        if not value:
            return value
        if value.lower().startswith(("data:", "blob:", "http://", "https://", "//")):
            return value
        if value.startswith("/"):
            return f"{base_url}{value}"
        if any(
            value.lower().endswith(ext)
            for ext in (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff")
        ):
            return f"{base_url}/{value.lstrip('/')}"
        return value

    @staticmethod
    def _base64_to_data_url(value: Any, mime_type: str = "image/jpeg") -> Any:
        """Turn a bare image base64 payload into a browser-loadable data URL."""
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if not stripped:
            return value
        if stripped.lower().startswith(("data:", "blob:", "http://", "https://", "//")):
            return stripped
        import re
        compact = "".join(stripped.split())
        if len(compact) < 64 or not re.fullmatch(r"[A-Za-z0-9+/=_-]+", compact):
            return value
        return f"data:{mime_type};base64,{compact}"

    @classmethod
    def _normalize_base64_artifacts(cls, value: Any, key: str = "") -> Any:
        """Normalize provider base64 image fields for direct browser rendering."""
        base64_keys = {
            "reference_base64", "reference_image_base64",
            "before_image_base64", "historical_image_base64",
            "current_image_base64", "current_with_changes_base64",
            "visualization_base64", "overlay_base64",
            "annotated_image_base64", "change_visualization_base64",
            "change_mask_base64", "change_map_base64",
            "mask_base64", "sar_mask_base64",
        }
        if isinstance(value, dict):
            return {k: cls._normalize_base64_artifacts(v, k.lower()) for k, v in value.items()}
        if isinstance(value, list):
            return [cls._normalize_base64_artifacts(v, key) for v in value]
        if isinstance(value, str):
            normalized_key = key.lower()
            if normalized_key in base64_keys or (
                "base64" in normalized_key
                and any(token in normalized_key for token in (
                    "image", "visual", "overlay", "mask", "change", "reference",
                    "historical", "before", "current", "artifact",
                ))
            ):
                return cls._base64_to_data_url(value)
        return value

    @classmethod
    def _normalize_artifacts(cls, value: Any, base_url: str, key: str = "") -> Any:
        artifact_keys = {
            "reference_image", "reference_image_url", "reference",
            "before_image", "before_image_url", "historical_image",
            "historical_image_url", "current_image", "current_image_url",
            "change_visualization", "change_visualization_url",
            "annotated_image", "annotated_image_url", "overlay_image",
            "overlay_image_url", "current_with_changes", "visualization",
            "visualization_url", "artifact_url", "image_url",
            "change_mask", "change_mask_url", "change_map", "mask_url",
            "sar_mask", "sar_mask_url",
        }

        if isinstance(value, dict):
            normalized = {
                k: cls._normalize_artifacts(v, base_url, k.lower())
                for k, v in value.items()
            }
            # Provider artifact objects commonly use {url/src/href/path/uri}.
            if key in artifact_keys:
                for nested_key in ("url", "src", "href", "path", "uri", "image_url"):
                    nested_value = normalized.get(nested_key)
                    if isinstance(nested_value, str):
                        normalized[nested_key] = cls._artifact_url(
                            nested_value,
                            base_url,
                        )
            return normalized
        if isinstance(value, list):
            return [cls._normalize_artifacts(v, base_url, key) for v in value]
        if isinstance(value, str) and key in artifact_keys:
            return cls._artifact_url(value, base_url)
        return value

    @staticmethod
    def _normalize_result(
        payload: dict,
        task: InvestigationTask,
    ) -> dict:
        """
        Preserve the ML provider response while exposing the fields expected
        by SatQuery's evidence/confidence pipeline when available.
        """
        result = payload.get("result")
        if isinstance(result, dict):
            normalized = dict(result)
        else:
            normalized = dict(payload)

        # Handle common confidence locations without inventing a value.
        confidence = normalized.get("confidence")
        if confidence is None:
            confidence = payload.get("confidence")
        if confidence is not None:
            try:
                normalized["confidence"] = float(confidence)
            except (TypeError, ValueError):
                pass

        evidence = normalized.get("evidence")
        if not isinstance(evidence, list):
            evidence = []

        if not evidence:
            evidence = [{
                "type": "temporal",
                "description": (
                    "Evidence returned by remote SatQuery ML "
                    f"single-image temporal analysis for task {task.task_id}."
                ),
                "source": "remote_ml",
                "metadata": {
                    "provider": "satquery-ml",
                },
            }]

        ml_artifact_base = (
            self_base_url
            if (self_base_url := getattr(settings, "ML_BASE_URL", "").strip().rstrip("/"))
            else settings.ML_FALLBACK_BASE_URL.strip().rstrip("/")
        )
        normalized = RemoteMLAdapter._normalize_artifacts(
            normalized,
            ml_artifact_base,
        )

        # Normalize bare base64 image artifacts returned by the ML job API.
        # The ML UI renders these as data:image/jpeg;base64,... resources.
        normalized = RemoteMLAdapter._normalize_base64_artifacts(normalized)
        normalized["evidence"] = evidence
        normalized["remote_ml"] = True
        return normalized

    def predict(
        self,
        task: InvestigationTask,
        image_paths: list[str],
        execution_context: dict | None = None,
    ) -> dict:
        if task.task_type != "change_analysis":
            raise ValueError(
                "RemoteMLAdapter currently supports only change_analysis."
            )

        if not image_paths:
            raise ValueError(
                "At least one image is required for remote ML inference."
            )

        if len(image_paths) != 1:
            raise ValueError(
                "Remote change analysis currently requires exactly one image."
            )

        # The current ML API exposes one image_base64 field. The comparison
        # years are supplied as metadata so the remote model can perform its
        # own temporal analysis.
        image_base64 = self._encode_image(image_paths[0])

        parameters = task.parameters or {}
        compare_year = str(
            parameters.get(
                "compare_year",
                settings.ML_DEFAULT_COMPARE_YEAR,
            )
        )
        current_year = str(
            parameters.get(
                "current_year",
                settings.ML_DEFAULT_CURRENT_YEAR,
            )
        )

        request_body = {
            "image_base64": image_base64,
            "compare_year": compare_year,
            "current_year": current_year,
            "mission": task.query or "Analyze temporal change.",
        }

        start_url = f"{self.base_url}/api/start"

        with httpx.Client(
            timeout=httpx.Timeout(self.timeout_seconds)
        ) as client:
            try:
                response = client.post(
                    start_url,
                    json=request_body,
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
            except (httpx.ConnectError, httpx.ConnectTimeout):
                # Cloudflare quick tunnels can change or become unreachable.
                # Retry the current SIH demo endpoint once instead of exposing
                # a low-level DNS error to the judge.
                if not self.fallback_base_url:
                    raise

                self.base_url = self.fallback_base_url
                start_url = f"{self.base_url}/api/start"
                response = client.post(
                    start_url,
                    json=request_body,
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()

            start_payload = response.json()
            job_id = start_payload.get("job_id")

            if not job_id:
                raise RuntimeError(
                    "Remote ML /api/start did not return a job_id."
                )

            deadline = time.monotonic() + self.timeout_seconds

            while time.monotonic() < deadline:
                status_response = client.get(
                    f"{self.base_url}/api/status/{job_id}",
                    headers={"Accept": "application/json"},
                )
                status_response.raise_for_status()

                status_payload = status_response.json()
                status, result_payload = (
                    self._extract_status_payload(status_payload)
                )

                normalized_status = str(
                    status or ""
                ).lower()

                if normalized_status in {
                    "completed",
                    "complete",
                    "done",
                    "success",
                    "succeeded",
                    "finished",
                }:
                    return self._normalize_result(
                        result_payload,
                        task,
                    )

                if normalized_status in {
                    "failed",
                    "error",
                    "cancelled",
                    "canceled",
                }:
                    raise RuntimeError(
                        "Remote ML job failed: "
                        + str(status_payload)
                    )

                time.sleep(
                    self.poll_interval_seconds
                )

        raise TimeoutError(
            "Remote ML inference timed out after "
            f"{self.timeout_seconds:.0f} seconds."
        )
