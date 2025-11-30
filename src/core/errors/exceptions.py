from fastapi import status
from .base_exception import AppException
from . import error_codes

class AlreadyExists(AppException):
    status_code = status.HTTP_409_CONFLICT
    code = error_codes.ALREADY_EXISTS
    
    def __init__(self, message = "The data you tried creating already exists"):
        super().__init__(message)

class NotFound(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    code = error_codes.NOT_FOUND
    
    def __init__(self, message = "The data you tried searching for does not exist"):
        super().__init__(message)

class InvalidSignature(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = error_codes.INVALID_SIGNATURE
    
    def __init__(self, message = "Authentication failed"):
        super().__init__(message)
