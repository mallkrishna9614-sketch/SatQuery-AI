def mock_vqa_handler(task):
    return {
        "answer": "A satellite scene containing land-cover features.",
        "confidence": 0.82,
        "evidence": [
            {
                "type": "visual",
                "description": "Relevant visual features detected in the input image."
            }
        ]
    }


def mock_caption_handler(task):
    return {
        "caption": "Satellite imagery showing a mixed land-cover scene.",
        "confidence": 0.80,
        "evidence": [
            {
                "type": "scene",
                "description": "Scene-level visual evidence from the input image."
            }
        ]
    }


def mock_grounding_handler(task):
    return {
        "regions": [],
        "confidence": 0.76,
        "evidence": [
            {
                "type": "spatial",
                "description": "Candidate region identified from the query."
            }
        ]
    }


def mock_change_handler(task):
    return {
        "change_detected": True,
        "change_type": "land-cover change",
        "confidence": 0.84,
        "evidence": [
            {
                "type": "temporal",
                "description": "Difference detected between the two temporal images."
            }
        ]
    }


def mock_optical_sar_handler(task):
    return {
        "finding": "Optical and SAR observations are available for cross-modal analysis.",
        "confidence": 0.81,
        "evidence": [
            {
                "type": "cross_modal",
                "description": "Evidence generated from optical and SAR inputs."
            }
        ]
    }