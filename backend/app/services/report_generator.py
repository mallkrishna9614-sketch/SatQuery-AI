from datetime import datetime, timezone
from pathlib import Path
import json

from app.core.config import settings


def generate_report(
    investigation_id: str,
    query: str,
    tasks,
    execution: dict,
) -> Path:

    report_data = {
        "report_version": "1.0",
        "investigation_id": investigation_id,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "query": query,

        "tasks": [
            task.model_dump(mode="json")
            if hasattr(task, "model_dump")
            else task
            for task in tasks
        ],

        "model_results": [
            result.model_dump(mode="json")
            if hasattr(result, "model_dump")
            else result
            for result in execution.get(
                "model_results",
                []
            )
        ],

        "evidence": [
            item.model_dump(mode="json")
            if hasattr(item, "model_dump")
            else item
            for item in execution.get(
                "evidence",
                []
            )
        ],

        "confidence": execution.get(
            "confidence",
            []
        ),

        "conflicts": execution.get(
            "conflicts",
            []
        ),

        "execution_trace": execution.get(
            "trace",
            []
        ),
    }

    report_path = (
        settings.report_dir
        / f"{investigation_id}.json"
    )

    with report_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report_data,
            file,
            indent=2,
            ensure_ascii=False
        )

    return report_path