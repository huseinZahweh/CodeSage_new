from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class APIError(HTTPException):
    def __init__(self, message: str, code: int = 400, details: dict = None):
        super().__init__(
            status_code=code,
            detail={"message": message, "details": details or {}}
        )

async def handle_api_error(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )
