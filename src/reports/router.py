from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from . import service, schemas, models
from src.auth.auth_dependencies import DB_SESSION, get_current_user, CURRENT_USER
from src.auth.models.user_account import User_Account
from src.core.schemas import APIResponse

router = APIRouter()

@router.post("/", response_model=APIResponse[schemas.ReportResponse], status_code=status.HTTP_201_CREATED)
async def create_report(
    data: schemas.ReportCreate,
    db: DB_SESSION,
    user: CURRENT_USER
):
    report = service.create_report(db, user, data)
    # Map pseudonym for response
    report_data = schemas.ReportResponse.from_orm(report)
    report_data.pseudonym = user.pseudonym
    return {"message": "Report created successfully", "code": 201, "data": report_data}

@router.get("/", response_model=APIResponse[schemas.FeedResponse])
async def get_feed(
    db: DB_SESSION,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    report_status: Optional[models.ReportStatus] = None
):
    reports, total = service.get_feed(db, page, limit, report_status)
    
    # Enrichment: add pseudonyms (In a real app, join in query)
    report_responses = []
    for r in reports:
        resp = schemas.ReportResponse.from_orm(r)
        if r.author:
            resp.pseudonym = r.author.pseudonym
        # Map comments pseudonyms
        for c, cr in zip(r.comments, resp.comments):
            if c.author:
                cr.pseudonym = c.author.pseudonym
        report_responses.append(resp)
        
    data = schemas.FeedResponse(reports=report_responses, total=total, page=page, limit=limit)
    return {"message": "Feed fetched successfully", "code": 200, "data": data}

@router.post("/{id}/vote", response_model=APIResponse[schemas.ReportResponse])
async def cast_vote(
    id: int,
    vote_data: schemas.VoteRequest,
    db: DB_SESSION,
    user: CURRENT_USER
):
    report = service.cast_vote(db, user, id, vote_data.vote_type)
    resp = schemas.ReportResponse.from_orm(report)
    if report.author:
        resp.pseudonym = report.author.pseudonym
    return {"message": "Vote recorded", "code": 200, "data": resp}

@router.post("/{id}/comments", response_model=APIResponse[schemas.CommentResponse])
async def add_comment(
    id: int,
    data: schemas.CommentCreate,
    db: DB_SESSION,
    user: CURRENT_USER
):
    comment = service.add_comment(db, user, id, data)
    resp = schemas.CommentResponse.from_orm(comment)
    resp.pseudonym = user.pseudonym
    return {"message": "Comment added", "code": 201, "data": resp}

@router.patch("/{id}/status", response_model=APIResponse[schemas.ReportResponse])
async def update_status(
    id: int,
    data: schemas.ReportUpdateStatus,
    db: DB_SESSION
):
    # TODO: Add admin check dependency here in the future
    report = service.update_report_status(db, id, data.status)
    resp = schemas.ReportResponse.from_orm(report)
    if report.author:
        resp.pseudonym = report.author.pseudonym
    return {"message": f"Status updated to {data.status}", "code": 200, "data": resp}
