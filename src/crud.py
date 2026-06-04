from sqlmodel import Session
from models import Paste
from schemas.paste import PasteCreate, PasteUpdate

def create_paste(session: Session, paste_in: PasteCreate) -> Paste:
    paste = Paste.model_validate(paste_in)
    session.add(paste)
    session.commit()
    session.refresh(paste)
    return paste

def _get_paste(session: Session, paste_id: int) -> Paste | None:
    return session.get(Paste, paste_id)

def get_paste(session: Session, paste_id: int) -> Paste | None:
    paste = _get_paste(session, paste_id)
    if paste:
        paste.view_count += 1
        session.add(paste)
        session.commit()
        session.refresh(paste)
    return paste

def update_paste(session: Session, paste_db: Paste, paste_in: PasteUpdate) -> Paste | None:
    paste_data = paste_in.model_dump(exclude_unset=True)
    for key, value in paste_data.items():
        setattr(paste_db, key, value)
    session.add(paste_db)
    session.commit()
    session.refresh(paste_db)
    return paste_db
        
    
def delete_paste(session: Session, paste_db: Paste) -> None:
    session.delete(paste_db)
    session.commit()
    return