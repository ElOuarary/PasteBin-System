from sqlmodel import Session, select, delete
from .models import Paste, User, Tag
from .schemas.paste import PasteCreate, PasteRead, PasteUpdate

from datetime import datetime, timezone
from typing import Optional
class PasteExpiredException(Exception):
    pass

def _is_expired(expires_at: datetime) -> bool:
    return expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)

def create_paste(session: Session, paste_in: PasteCreate) -> PasteRead:
    paste = Paste.model_validate(paste_in)
    tag = None
    if paste_in.tag is not None:
        statement = select(Tag).where(Tag.name == paste_in.tag)
        tag = session.exec(statement).first()
        if tag is None:
            tag = Tag(name=paste_in.tag)
            session.add(tag)
            session.commit()
            session.refresh(tag)
        paste.tag_id = tag.id
    session.add(paste)
    session.commit()
    session.refresh(paste)
    paste_read = PasteRead.model_validate(paste)
    if tag is not None: paste_read.tag = tag.name
    return paste_read

def _get_paste(session: Session, paste_id: Optional[int] = None, user: Optional[str] = None, tag: Optional[str] = None) -> Paste | None:
    user_model, tag_model = None, None
    if user is not None:
        user_model = session.exec(select(User).where(User.name == user)).first()
    if tag is not None:
        tag_model = session.exec(select(Tag).where(Tag.name == tag)).first()
        
    if paste_id is not None:
        if user_model is not None  and tag_model is not None:
            return session.exec(select(Paste).where(Paste.id == paste_id).where(Paste.user_id == user_model.id).where(Paste.tag_id == tag_model.id)).first()
        elif user_model is not None:
            return session.exec(select(Paste).where(Paste.id == paste_id).where(Paste.user_id == user_model.id)).first()
        elif tag_model is not None:
            return session.exec(select(Paste).where(Paste.id == paste_id).where(Paste.tag_id == tag_model.id)).first()
        else:
            return session.get(Paste, paste_id)
    else:
        if user_model is not None  and tag_model is not None:
            return session.exec(select(Paste).where(Paste.user_id == user_model.id).where(Paste.tag_id == tag_model.id)).first()
        elif user_model is not None:
            return session.exec(select(Paste).where(Paste.user_id == user_model.id)).first()
        elif tag_model is not None:
            return session.exec(select(Paste).where(Paste.tag_id == tag_model.id)).first()

def get_paste(session: Session, paste_id: Optional[int] = None, user: Optional[str] = None, tag: Optional[str] = None) -> PasteRead | None:
    paste = _get_paste(session, paste_id, user, tag)
    if paste:
        if paste.expires_at is not None and _is_expired(paste.expires_at):
            raise PasteExpiredException
        paste.view_count += 1
        session.add(paste)
        session.commit()
        session.refresh(paste)
        
        paste_read = PasteRead.model_validate(paste)
        if paste.user_id is not None:
            user = session.exec(select(User).where(User.id == paste.user_id)).first()
            if user is not None:
                paste_read.user = user.name
        if paste.tag_id is not None:
            tag = session.exec(select(Tag).where(Tag.id == paste.tag_id)).first()
            if tag is not None:
                paste_read.tag = tag.name
        return paste_read
    return paste

def update_paste(session: Session, paste_db: Paste, paste_in: PasteUpdate) -> PasteRead | None:
    paste_data = paste_in.model_dump(exclude_unset=True)
    for key, value in paste_data.items():
        if key == "tag":
            tag = session.exec(select(Tag).where(Tag.name == paste_in.tag)).first()
            if tag is None:
                session.add(Tag(name=value))
                session.commit()
                tag = session.exec(select(Tag).where(Tag.name == paste_in.tag)).first()
            setattr(paste_db, "tag_id", tag.id)
            continue
        setattr(paste_db, key, value)
    session.add(paste_db)
    session.commit()
    session.refresh(paste_db)
    
    paste_read = PasteRead.model_validate(paste_db)
    
    if paste_db.tag_id is not None:
        tag = session.exec(select(Tag).where(Tag.id == paste_db.tag_id)).first()
        if tag is not None:
            paste_read.tag = tag.name
        return paste_read
    return paste_read
        
    
def delete_paste(session: Session, paste_db: Paste) -> None:
    session.delete(paste_db)
    session.commit()
    return

def delete_expired(session: Session) -> None:
    session.exec(delete(Paste).where(Paste.expires_at < datetime.now(timezone.utc)))
    return