import uuid
from app.services.report_generator import generate_report
from fastapi import APIRouter
from fastapi import APIRouter, HTTPException
from app.schemas.investigation import (
    InvestigationRequest,
    InvestigationResponse,
)
from app.services.investigation_repository import (
    save_investigation,
    get_investigation,
)

from app.services.mission_agent import build_investigation_plan
from app.services.plan_validator import validate_plan
from app.services.investigation_pipeline import run_investigation
from app.services.investigation_repository import save_investigation


router = APIRouter(
    prefix="/investigations",
    tags=["investigations"]
)


@router.post("/", response_model=InvestigationResponse)
def create_investigation(request: InvestigationRequest):

    # 1. Create investigation ID
    investigation_id = "inv_" + uuid.uuid4().hex[:12]

    # 2. Build investigation plan
    tasks = build_investigation_plan(
        query=request.query,
        image_ids=request.image_ids
    )

    # 3. Validate investigation plan
    validation = validate_plan(tasks)

    if not validation["valid"]:
        return {
            "investigation_id": investigation_id,
            "status": "failed",
            "query": request.query,
            "tasks": tasks,
            "execution": None,
            "message": (
                "Investigation plan is invalid: "
                + " ".join(validation["errors"])
            )
        }

    # 4. Execute investigation
    pipeline_result = run_investigation(tasks)

    # 5. Check whether execution succeeded
    failed_tasks = [
        result
        for result in pipeline_result["execution_results"]
        if not result["success"]
    ]

    # 6. Handle failed execution
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
            "message": "One or more investigation tasks failed."
        }

    # 7. Save successful investigation
    save_investigation(
        investigation_id=investigation_id,
        query=request.query,
        status="completed",
        tasks=tasks,
        execution=pipeline_result,
    )
    report_path = generate_report(
    investigation_id=investigation_id,
    query=request.query,
    tasks=tasks,
    execution=pipeline_result,
    )

    # 8. Return complete investigation
    return {
        "investigation_id": investigation_id,
        "status": "completed",
        "query": request.query,
        "tasks": tasks,
        "execution": pipeline_result,
        "message": "Investigation completed successfully."
    }
@router.get("/{investigation_id}")
def get_investigation_by_id(investigation_id: str):

    investigation = get_investigation(
        investigation_id
    )

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail="Investigation not found."
        )

    return investigation