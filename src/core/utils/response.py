from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Any, Optional

def SuccessResponse(message:str, code: int = 200, data: Optional[Any] = None)-> JSONResponse:
    return JSONResponse(status_code=code, content={
        "message": message,
        "code": code,
        "error": None,
        "data": jsonable_encoder(data)
    })

def ErrorResponse(
    message: str,
    code: int = 400,
    error: Optional[str] = None
) -> JSONResponse:
    return JSONResponse(
        status_code=code,
        content={
            "message": message,
            "code": code,
            "error": error or message,
            "data": None,
        }
    )
