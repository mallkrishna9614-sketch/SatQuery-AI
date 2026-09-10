from app.services.conflict_engine import detect_conflicts


def test_change_model_conflict():
    results = [
        {
            "success": True,
            "task_id": "task_1",
            "result": {
                "change_detected": True
            }
        },
        {
            "success": True,
            "task_id": "task_2",
            "result": {
                "change_detected": False
            }
        }
    ]

    conflicts = detect_conflicts(results)

    assert len(conflicts) == 1
    assert conflicts[0]["type"] == "model_disagreement"
    assert conflicts[0]["severity"] == "high"


def test_no_conflict():
    results = [
        {
            "success": True,
            "task_id": "task_1",
            "result": {
                "change_detected": True
            }
        },
        {
            "success": True,
            "task_id": "task_2",
            "result": {
                "change_detected": True
            }
        }
    ]

    conflicts = detect_conflicts(results)

    assert conflicts == []