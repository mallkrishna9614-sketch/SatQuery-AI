from typing import Any


def mock_vqa_handler(
    task,
    execution_context: dict[str, Any] | None = None
):
    return {
        "answer": "A satellite scene containing land-cover features.",
        "confidence": 0.82,
        "evidence": [
            {
                "type": "visual",
                "description": (
                    "Relevant visual features detected "
                    "in the input image."
                )
            }
        ]
    }


def mock_caption_handler(
    task,
    execution_context: dict[str, Any] | None = None
):
    return {
        "caption": (
            "Satellite imagery showing a mixed "
            "land-cover scene."
        ),
        "confidence": 0.80,
        "evidence": [
            {
                "type": "scene",
                "description": (
                    "Scene-level visual evidence "
                    "from the input image."
                )
            }
        ]
    }


def mock_grounding_handler(
    task,
    execution_context: dict[str, Any] | None = None
):
    previous_results = {}

    if execution_context:
        previous_results = execution_context.get(
            "previous_results",
            {}
        )

    return {
        "regions": [
            {
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 150
            }
        ],
        "context_received": bool(
            previous_results
        ),
        "confidence": 0.76,
        "evidence": [
            {
                "type": "spatial",
                "description": (
                    "Candidate region identified "
                    "using upstream investigation evidence."
                ),
                "metadata": {
                    "upstream_tasks": list(
                        previous_results.keys()
                    )
                }
            }
        ]
    }


def mock_change_handler(
    task,
    execution_context: dict[str, Any] | None = None
):
    return {
        "change_detected": True,
        "change_type": "land-cover change",
        "confidence": 0.84,
        "evidence": [
            {
                "type": "temporal",
                "description": (
                    "Difference detected between "
                    "the two temporal images."
                )
            }
        ]
    }


def mock_optical_sar_handler(
    task,
    execution_context: dict[str, Any] | None = None
):
    return {
        "finding": (
            "Optical and SAR observations are "
            "available for cross-modal analysis."
        ),
        "confidence": 0.81,
        "evidence": [
            {
                "type": "cross_modal",
                "description": (
                    "Evidence generated from optical "
                    "and SAR inputs."
                )
            }
        ]
    }