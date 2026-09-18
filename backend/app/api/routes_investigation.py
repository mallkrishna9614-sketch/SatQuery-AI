import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.schemas.investigation import (
    InvestigationRequest,
    InvestigationResponse,
)

from app.services.mission_agent import build_investigation_plan
from app.services.plan_validator import validate_plan
from app.services.investigation_pipeline import run_investigation

from app.services.investigation_repository import (
    save_investigation,
    get_investigation,
)

from app.services.report_generator import generate_report
from app.core.config import settings


router = APIRouter(
    prefix="/investigations",
    tags=["investigations"]
)


@router.post(
    "/",
    response_model=InvestigationResponse
)
def create_investigation(
    request: InvestigationRequest
):

    # -------------------------------------------------
    # 1. Create investigation ID
    # -------------------------------------------------

    investigation_id = (
        "inv_"
        + uuid.uuid4().hex[:12]
    )

    # -------------------------------------------------
    # 2. Build investigation plan
    # -------------------------------------------------

    tasks = build_investigation_plan(
        query=request.query,
        image_ids=request.image_ids
    )

    # -------------------------------------------------
    # 3. Validate investigation plan
    # -------------------------------------------------

    validation = validate_plan(tasks)

    if not validation["valid"]:

        save_investigation(
            investigation_id=investigation_id,
            query=request.query,
            status="failed",
            tasks=tasks,
            execution=None,
        )

        return {
            "investigation_id": investigation_id,
            "status": "failed",
            "query": request.query,
            "tasks": tasks,
            "execution": None,
            "message": (
                "Investigation plan is invalid: "
                + " ".join(
                    validation["errors"]
                )
            )
        }

    # -------------------------------------------------
    # 4. Execute investigation
    # -------------------------------------------------

    pipeline_result = run_investigation(
        tasks
    )

    # -------------------------------------------------
    # 5. Check execution status
    # -------------------------------------------------

    failed_tasks = [
        result
        for result in pipeline_result[
            "execution_results"
        ]
        if not result["success"]
    ]

    # -------------------------------------------------
    # 6. Handle failed execution
    # -------------------------------------------------

    if failed_tasks:

        save_investigation(
            investigation_id=investigation_id,
            query=request.query,
            status="failed",
            tasks=tasks,
            execution=pipeline_result,
        )

        return {
            "investigation_id": investigation_id,
            "status": "failed",
            "query": request.query,
            "tasks": tasks,
            "execution": pipeline_result,
            "message": (
                "One or more investigation "
                "tasks failed."
            )
        }

    # -------------------------------------------------
    # 7. Save successful investigation
    # -------------------------------------------------

    save_investigation(
        investigation_id=investigation_id,
        query=request.query,
        status="completed",
        tasks=tasks,
        execution=pipeline_result,
    )

    # -------------------------------------------------
    # 8. Generate investigation report
    # -------------------------------------------------

    generate_report(
        investigation_id=investigation_id,
        query=request.query,
        tasks=tasks,
        execution=pipeline_result,
    )

    # -------------------------------------------------
    # 9. Return complete investigation
    # -------------------------------------------------

    return {
        "investigation_id": investigation_id,
        "status": "completed",
        "query": request.query,
        "tasks": tasks,
        "execution": pipeline_result,
        "finding": pipeline_result.get("finding"),
        "message": (
            "Investigation completed successfully."
        )
    }


# -----------------------------------------------------
# Get saved investigation
# -----------------------------------------------------

@router.get(
    "/{investigation_id}"
)
def get_investigation_by_id(
    investigation_id: str
):

    investigation = get_investigation(
        investigation_id
    )

    if investigation is None:

        raise HTTPException(
            status_code=404,
            detail="Investigation not found."
        )

    return investigation


# -----------------------------------------------------
# Download investigation report
# -----------------------------------------------------

@router.get(
    "/{investigation_id}/report"
)
def get_investigation_report(
    investigation_id: str
):

    # Make sure investigation exists
    investigation = get_investigation(
        investigation_id
    )

    if investigation is None:

        raise HTTPException(
            status_code=404,
            detail="Investigation not found."
        )

    report_path = (
        settings.report_dir
        / f"{investigation_id}.json"
    )

    if not report_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Investigation report not found."
        )

    return FileResponse(
        path=report_path,
        media_type="application/json",
        filename=(
            f"{investigation_id}_report.json"
        )
    )