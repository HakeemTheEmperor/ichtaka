from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from . import service, schemas
from src.auth.auth_dependencies import DB_SESSION, CURRENT_USER
from src.core.schemas import APIResponse
from src.core.utils.response import SuccessResponse

router = APIRouter()

@router.get("", response_model=APIResponse[List[schemas.NotificationResponse]])
async def get_notifications(
    db: DB_SESSION,
    user: CURRENT_USER
):
    notifications = service.get_notifications(db, user.id)
    # Convert to response schema
    resp_data = []
    for n in notifications:
        item = schemas.NotificationResponse.from_orm(n)
        item.sender_pseudonym = n.sender.pseudonym if n.sender else None
        resp_data.append(item)
        
    return SuccessResponse(message="Notifications fetched", data=resp_data)

@router.post("/{id}/read", response_model=APIResponse[bool])
async def mark_as_read(
    id: int,
    db: DB_SESSION,
    user: CURRENT_USER
):
    success = service.mark_as_read(db, id, user.id)
    return SuccessResponse(message="Notification marked as read", data=success)

@router.post("/read-all", response_model=APIResponse[bool])
async def mark_all_as_read(
    db: DB_SESSION,
    user: CURRENT_USER
):
    success = service.mark_all_as_read(db, user.id)
    return SuccessResponse(message="All notifications marked as read", data=success)
