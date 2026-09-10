from typing import Any


def detect_conflicts(
    model_results: list[dict[str, Any]]
) -> list[dict[str, Any]]:

    conflicts = []

    successful_results = [
        result
        for result in model_results
        if result.get("success")
    ]

    for i in range(len(successful_results)):
        for j in range(i + 1, len(successful_results)):

            first = successful_results[i]
            second = successful_results[j]

            first_result = first.get("result") or {}
            second_result = second.get("result") or {}

            # Change detection conflict
            if (
                "change_detected" in first_result
                and "change_detected" in second_result
            ):
                if (
                    first_result["change_detected"]
                    != second_result["change_detected"]
                ):
                    conflicts.append({
                        "type": "model_disagreement",
                        "task_ids": [
                            first["task_id"],
                            second["task_id"]
                        ],
                        "description": (
                            "Specialist models disagree about "
                            "whether change was detected."
                        ),
                        "severity": "high"
                    })

            # General answer conflict
            if (
                "answer" in first_result
                and "answer" in second_result
            ):
                if first_result["answer"] != second_result["answer"]:
                    conflicts.append({
                        "type": "answer_disagreement",
                        "task_ids": [
                            first["task_id"],
                            second["task_id"]
                        ],
                        "description": (
                            "Specialist models produced "
                            "different answers."
                        ),
                        "severity": "medium"
                    })

    return conflicts