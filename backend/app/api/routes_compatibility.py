from fastapi import APIRouter

from app.schemas.image import (
    CompatibilityRequest,
    CompatibilityResponse
)

from app.services.compatibility import (
    check_compatibility
)


router = APIRouter(
    prefix="/compatibility",
    tags=["compatibility"]
)


@router.post(
    "/check",
    response_model=CompatibilityResponse
)
def compatibility_check(
    request: CompatibilityRequest
):

    result = check_compatibility(
        image_ids=request.image_ids,
        check_type=request.check_type
    )

    return CompatibilityResponse(
        compatible=result["compatible"],
        reasons=result["reasons"],
        images=result["images"]
    )