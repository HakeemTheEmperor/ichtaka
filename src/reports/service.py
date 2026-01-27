from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import Report, Comment, Vote, ReportStatus, VoteType
from .schemas import ReportCreate, CommentCreate, VoteRequest
from src.auth.models.user_account import User_Account
from fastapi import HTTPException, status

def create_report(db: Session, user: User_Account, data: ReportCreate):
    new_report = Report(
        user_id=user.id,
        title=data.title,
        description=data.description,
        image_url=data.image_url,
        location=data.location,
        source_url=data.source_url
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

def get_feed(db: Session, page: int = 1, limit: int = 10, status_filter: ReportStatus = None):
    query = db.query(Report)
    if status_filter:
        query = query.filter(Report.status == status_filter)
    
    total = query.count()
    reports = query.order_by(Report.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return reports, total

def add_comment(db: Session, user: User_Account, report_id: int, data: CommentCreate):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    new_comment = Comment(
        report_id=report_id,
        user_id=user.id,
        content=data.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment

def cast_vote(db: Session, user: User_Account, report_id: int, vote_type: VoteType):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    existing_vote = db.query(Vote).filter(
        Vote.report_id == report_id,
        Vote.user_id == user.id
    ).first()
    
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            # Toggle off
            db.delete(existing_vote)
            if vote_type == VoteType.UPVOTE:
                report.upvotes_count -= 1
            else:
                report.downvotes_count -= 1
        else:
            # Change vote type
            old_type = existing_vote.vote_type
            existing_vote.vote_type = vote_type
            if vote_type == VoteType.UPVOTE:
                report.upvotes_count += 1
                report.downvotes_count -= 1
            else:
                report.downvotes_count += 1
                report.upvotes_count -= 1
    else:
        # New vote
        new_vote = Vote(
            report_id=report_id,
            user_id=user.id,
            vote_type=vote_type
        )
        db.add(new_vote)
        if vote_type == VoteType.UPVOTE:
            report.upvotes_count += 1
        else:
            report.downvotes_count += 1
            
    db.commit()
    db.refresh(report)
    return report

def update_report_status(db: Session, report_id: int, new_status: ReportStatus):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.status = new_status
    db.commit()
    db.refresh(report)
    return report
