from fastapi import Request, status
from fastapi.responses import JSONResponse
from .base_exception import AppException
from .error_codes import UNEXPECTED_ERROR
from ..utils.response import ErrorResponse

async def app_exception_handler(request: Request, exc: AppException):
    """Handles all controlled AppExceptions."""
    return ErrorResponse(code=exc.status_code, message=exc.message, error=exc.code)
    
async def unhandled_exception_handler(request: Request, exc: Exception):
    return ErrorResponse(code=status.HTTP_500_INTERNAL_SERVER_ERROR, message="Internal Server error", error=UNEXPECTED_ERROR)