from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, delete, select, update

from src.models import Paste, Tag, User
from src.schemas.paste import PasteCreate, PasteRead, PasteUpdate


def _is_expired(expires_at: datetime) -> bool:
    return expires_at < datetime.now(UTC)


def create_paste(session: Session, paste_in: PasteCreate, user: User) -> PasteRead:
    paste_data = paste_in.model_dump(exclude={"tags"})
    paste = Paste(**paste_data)
    paste.user_id = user.id
    paste.linked_user = user

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
    username: str | None = None,
    tag: str | None = None,
) -> list[Paste]:
    if username is None and tag is None:
        return None

    statement = select(Paste).options(
        selectinload(Paste.linked_user), selectinload(Paste.linked_tags)
    )

    if username is not None:
        statement = statement.join(User, Paste.user_id == User.id).where(
            User.username == username
        )

    if tag is not None:
        statement = statement.where(Paste.linked_tags.any(Tag.name == tag))

    return session.exec(statement).all()


def _validate_paste_list(
    pastes: list[Paste] | None, user: User, search: bool = False
) -> list[Paste]:
    if pastes is None or len(pastes) == 0:
        if search:
            return []
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"}
        )
    elif (
        len(pastes) == 1
        and pastes[0].expires_at is not None
        and _is_expired(pastes[0].expires_at)
    ):
        if search:
            return []
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"error": "content no longer available"},
        )
    else:
        return [
            paste
            for paste in pastes
            if (not paste.is_private or paste.user_id == user.id)
            and (paste.expires_at is None or not _is_expired(paste.expires_at))
        ]


def _serialize_pastes(
    session: Session, pastes: list[Paste], search: bool = False
) -> list[PasteRead]:
    if len(pastes) == 1 and not search:
        statement = (
            update(Paste)
            .where(Paste.id == pastes[0].id)
            .values(view_count=pastes[0].view_count + 1)
        )
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
    user: User,
    paste_id: int | None = None,
    username: str | None = None,
    tag: str | None = None,
) -> list[PasteRead] | None:
    if paste_id is not None:
        paste_db: Paste = get_validate_paste(session, paste_id, user)
        return [paste_db]
    else:
        paste_db: list[Paste] = _get_paste(session, username, tag)
        paste_db: list[Paste] = _validate_paste_list(paste_db, user)
        search = False if paste_id is not None else True
        return _serialize_pastes(session, paste_db, search=search)


def search_pastes(
    session: Session,
    user: User,
    keyword: str,
    limit: int | None = 1000,
    offset: int | None = 0,
) -> list[PasteRead]:
    paste_db: list[Paste] = session.exec(
        select(Paste)
        .options(selectinload(Paste.linked_tags), selectinload(Paste.linked_user))
        .where(col(Paste.content).ilike(f"%{keyword}%"))
        .limit(limit)
        .offset(offset)
    ).all()
    paste_db: list[Paste] = _validate_paste_list(paste_db, user, search=True)
    return _serialize_pastes(session, paste_db, search=True)


def update_paste(
    session: Session, paste_db: Paste, paste_in: PasteUpdate
) -> PasteRead | None:
    paste_data = paste_in.model_dump(exclude_unset=True)
    statement = update(Paste).where(Paste.id == paste_db.id)
    updates = {}
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

        updates[key] = value

    if len(updates) > 0:
        statement = statement.values(**updates)
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


def delete_expired(session: Session) -> None:
    session.exec(delete(Paste).where(Paste.expires_at < datetime.now(UTC)))
    session.commit()


def validate_paste(paste_db: Paste, user: User):
    if paste_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"}
        )
    elif paste_db.expires_at is not None and _is_expired(paste_db.expires_at):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"error": "content no longer available"},
        )
    elif paste_db.is_private and paste_db.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "can't access this resource"},
        )


def get_validate_paste(session: Session, paste_id: int, user: User):
    paste_db = session.get(Paste, paste_id)
    validate_paste(paste_db, user)
    return paste_db
