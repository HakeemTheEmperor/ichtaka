from sqlalchemy.orm import Session
from .models import Notification, NotificationType
from .schemas import NotificationCreate
from src.core.websocket_manager import manager
from src.auth.models import User_Account

async def create_notification(
    db: Session, 
    recipient_id: int, 
    type: str, 
    message: str, 
    sender_id: int = None, 
    post_id: str = None
):
    # Save to DB
    new_notif = Notification(
        recipient_id=recipient_id,
        sender_id=sender_id,
        type=type,
        message=message,
        post_id=post_id
    )
    db.add(new_notif)
    db.commit()
    db.refresh(new_notif)
    
    # Notify via WebSocket
    sender = db.query(User_Account).filter(User_Account.id == sender_id).first() if sender_id else None
    
    payload = {
        "type": "notification",
        "data": {
            "id": new_notif.id,
            "type": new_notif.type,
            "message": new_notif.message,
            "post_id": new_notif.post_id,
            "sender_pseudonym": sender.pseudonym if sender else None,
            "created_at": new_notif.created_at.isoformat(),
            "is_read": new_notif.is_read
        }
    }
    await manager.send_personal_message(payload, recipient_id)
    return new_notif

def get_notifications(db: Session, user_id: int, limit: int = 50):
    return db.query(Notification).filter(Notification.recipient_id == user_id).order_by(Notification.created_at.desc()).limit(limit).all()

def mark_as_read(db: Session, notif_id: int, user_id: int):
    notif = db.query(Notification).filter(Notification.id == notif_id, Notification.recipient_id == user_id).first()
    if notif:
        notif.is_read = True
        db.commit()
        return True
    return False

def mark_all_as_read(db: Session, user_id: int):
    db.query(Notification).filter(Notification.recipient_id == user_id, Notification.is_read == False).update({"is_read": True})
    db.commit()
    return True
