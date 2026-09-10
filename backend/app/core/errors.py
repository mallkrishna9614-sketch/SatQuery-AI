from fastapi import Request
from fastapi.responses import JSONResponse


class SatQueryError(Exception):

    def __init__(
        self,
        code: str,
        message: str,
        details=None,
        status_code: int = 400
    ):
        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code


async def satquery_error_handler(
    request: Request,
    exc: SatQueryError
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )