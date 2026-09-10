import uuid

from fastapi import APIRouter
from app.services.plan_validator import validate_plan
from app.schemas.investigation import (
    InvestigationRequest,
    InvestigationResponse
)

from app.services.mission_agent import (
    build_investigation_plan
)


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

    investigation_id = (
        "inv_"
        + uuid.uuid4().hex[:12]
    )

    # -----------------------------
    # 1. Mission Agent
    # -----------------------------

    tasks = build_investigation_plan(
        query=request.query,
        image_ids=request.image_ids
    )

    # -----------------------------
    # 2. Validate investigation plan
    # -----------------------------

    validation = validate_plan(tasks)

    if not validation["valid"]:

        return InvestigationResponse(
            investigation_id=investigation_id,
            status="failed",
            query=request.query,
            tasks=tasks,
            message="Investigation plan is invalid: "
                    + " ".join(validation["errors"])
        )

    # -----------------------------
    # 3. Valid plan
    # -----------------------------

    return InvestigationResponse(
        investigation_id=investigation_id,
        status="queued",
        query=request.query,
        tasks=tasks,
        message="Investigation created successfully."
    )