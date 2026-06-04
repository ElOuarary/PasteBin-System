from sqlmodel import Session, select
from .models import Paste, Tag
from .schemas.paste import PasteCreate, PasteRead, PasteUpdate

from datetime import datetime, timezone

class PasteExpiredException(Exception):
    pass

def _is_expired(expires_at: datetime) -> bool:
    return expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)

def create_paste(session: Session, paste_in: PasteCreate) -> PasteRead:
    paste = Paste.model_validate(paste_in)
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
    if tag is not None:paste_read.tag = tag.name
    return paste_read

def _get_paste(session: Session, paste_id: int) -> Paste | None:
    return session.get(Paste, paste_id)

def get_paste(session: Session, paste_id: int) -> PasteRead | None:
    paste = _get_paste(session, paste_id)
    if paste:
        if paste.expires_at is not None and _is_expired(paste.expires_at):
            raise PasteExpiredException
        paste.view_count += 1
        session.add(paste)
        session.commit()
        session.refresh(paste)
        
        paste_read = PasteRead.model_validate(paste)
        if paste.tag_id is not None:
            tag = session.exec(select(Tag).where(Tag.id == paste.tag_id)).first()
            if tag is not None:
                paste_read.tag = tag.name
        return paste_read
    return paste

def update_paste(session: Session, paste_db: Paste, paste_in: PasteUpdate) -> PasteRead | None:
    paste_data = paste_in.model_dump(exclude_unset=True)
    for key, value in paste_data.items():
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