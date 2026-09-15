from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlmodel import Session, col, select, update

from .models import Paste, PasteTagLink, Tag, User
from .schemas.paste import PasteCreate, PasteRead, PasteUpdate


def _is_expired(expires_at: datetime) -> bool:
    return expires_at < datetime.now(UTC)


def create_paste(session: Session, paste_in: PasteCreate) -> PasteRead:
    paste_data = paste_in.model_dump(exclude={"tags"})
    paste = Paste(**paste_data)

    if paste_in.tags:
        statement = select(Tag).where(Tag.name.in_(paste_in.tags))
        existing_tags = session.exec(statement).all()
        existing_names = {tag.name for tag in existing_tags}

        missing_tags = [
            Tag(name=name) for name in paste_in.tags if name not in existing_names
        ]

        tags = list(existing_tags) + missing_tags
        paste.linked_tags = tags

    session.add(paste)
    session.commit()
    session.refresh(paste)

    paste_read = PasteRead.model_validate(paste)
    if paste.linked_tags:
        paste_read.tags = [tag.name for tag in paste.linked_tags]

    return paste_read


def _get_paste(
    session: Session,
    paste_id: int | None = None,
    name: str | None = None,
    tag: str | None = None,
) -> list[Paste]:
    if paste_id is None and name is None and tag is None:
        return None

    statement = select(Paste)

    if paste_id is not None:
        statement = statement.where(Paste.id == paste_id)

    if name is not None:
        statement = statement.join(User, Paste.user_id == User.id).where(
            User.name == name
        )

    if tag is not None:
        statement = (
            statement.join(PasteTagLink, PasteTagLink.paste_id == Paste.id)
            .join(Tag, Tag.id == PasteTagLink.tag_id)
            .where(Tag.name == tag)
        )

    return session.exec(statement).all()


def _validate_paste_list(pastes: list[Paste] | None) -> list[Paste]:
    if pastes is None or len(pastes) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"}
        )
    elif len(pastes) == 1 and pastes[0].expires_at is not None and _is_expired(pastes[0].expires_at):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail={"error": "not found"})
    else:
        for paste in pastes:
            if paste.expires_at is not None and _is_expired(paste.expires_at):
                pastes.remove(paste)
        return pastes


def helper_func(session: Session, pastes: list[Paste]) -> list[PasteRead]:
    if len(pastes) == 1:
        statement = update(Paste).where(Paste.id == pastes[0].id).values(view_count=pastes[0].view_count + 1)
        session.exec(statement)
        session.commit()
        session.refresh(pastes[0])

    pastes_read = []
    for paste in pastes:
        paste_read = PasteRead.model_validate(paste)
        if paste.linked_user is not None:
            paste_read.user = paste.linked_user.name
        if paste.linked_tags is not None:
            paste_read.tags = [tag.name for tag in paste.linked_tags]
        pastes_read.append(paste_read)

    return pastes_read

def get_paste(
    session: Session,
    paste_id: int | None = None,
    user: str | None = None,
    tag: str | None = None,
) -> list[PasteRead] | None:
    paste_db: list[Paste] = _get_paste(session, paste_id, user, tag)
    paste_db: list[Paste] = _validate_paste_list(paste_db)
    return helper_func(session, paste_db)


def search_pastes(session: Session, keyword: str, limit: int | None = 1000, offset: int | None = 0) -> list[PasteRead]:
    paste_db: list[Paste] = session.exec(select(Paste).where(col(Paste.content).ilike(f"%{keyword}%")).limit(limit).offset(offset)).all()
    paste_db: list[Paste] = _validate_paste_list(paste_db)
    return helper_func(session, paste_db)

def update_paste(
    session: Session, paste_db: Paste, paste_in: PasteUpdate
) -> PasteRead | None:
    paste_data = paste_in.model_dump(exclude_unset=True)
    statement = update(Paste).where(Paste.id == paste_db.id)
    for key, value in paste_data.items():
        if key == "tags":
            if value is not None:
                existing_tags = session.exec(
                    select(Tag).where(col(Tag.name).in_(value))
                ).all()
                if len(existing_tags) != 0:
                    missing_tags = [
                        Tag(name=name)
                        for name in value
                        if name not in {tag.name for tag in existing_tags}
                    ]
                else:
                    missing_tags = [Tag(name=name) for name in value]
                tags = list(existing_tags) + missing_tags
                paste_db.linked_tags = tags
            continue
        statement = statement.values({key: value})
    session.exec(statement)
    session.commit()

    session.refresh(paste_db)
    paste_read = PasteRead.model_validate(paste_db)

    if paste_db.linked_tags is not None:
        paste_read.tags = [tag.name for tag in paste_db.linked_tags]
    return paste_read


def delete_paste(session: Session, paste_db: Paste) -> None:
    session.delete(paste_db)
    session.commit()


# Not reliable for now as It only deletes the records in the Paste table, without removing the associated one in PasteTag
def delete_expired(session: Session) -> None:
    expired = session.exec(select(Paste).where(Paste.expires_at < datetime.now(UTC))).all()
    if expired:
        for paste in expired:
            paste.linked_tags.clear()
            session.add(paste)
            session.delete(paste)
        session.commit()


def validate_paste(paste_db: Paste):
    if paste_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"}
        )
    elif paste_db.expires_at is not None and _is_expired(paste_db.expires_at):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"error": "content no longer available"},
        )


def get_validate_paste(session: Session, paste_id: int):
    paste_db = session.get(Paste, paste_id)
    validate_paste(paste_db)
    return paste_db
