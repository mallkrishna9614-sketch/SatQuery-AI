import json
from datetime import datetime, timezone

from app.core.database import get_connection


def save_investigation(
    investigation_id: str,
    query: str,
    status: str,
    tasks,
    execution=None,
):
    connection = get_connection()

    # Convert Pydantic models to JSON-safe dictionaries
    tasks_data = [
        task.model_dump(mode="json")
        for task in tasks
    ]

    execution_data = None

    if execution is not None:
        execution_data = {
            "execution_results": execution.get(
                "execution_results",
                []
            ),
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
            "trace": execution.get(
                "trace",
                []
            ),
        }

    connection.execute(
        """
        INSERT OR REPLACE INTO investigations (
            investigation_id,
            query,
            status,
            tasks,
            execution,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            investigation_id,
            query,
            status,
            json.dumps(tasks_data),
            json.dumps(execution_data)
            if execution_data is not None
            else None,
            datetime.now(timezone.utc).isoformat(),
        )
    )

    connection.commit()
    connection.close()


def get_investigation(investigation_id: str):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM investigations
        WHERE investigation_id = ?
        """,
        (investigation_id,)
    ).fetchone()

    connection.close()

    if row is None:
        return None

    return {
        "investigation_id": row["investigation_id"],
        "query": row["query"],
        "status": row["status"],
        "tasks": json.loads(row["tasks"]),
        "execution": (
            json.loads(row["execution"])
            if row["execution"]
            else None
        ),
        "created_at": row["created_at"],
    }