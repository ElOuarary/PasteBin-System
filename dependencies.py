from typing import Annotated

from fastapi import Header, HTTPException, status


def content_type_validation(
    content_type: Annotated[str, Header()] = "application/json",
):
    if content_type.lower() != "application/json":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="application/json is the only supported value for the Content-Type",
        )


def accept_validation(accept: Annotated[str, Header()] = "application/json"):
    if accept.lower() not in ("*/*", "application/json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="application/json is only supported value for the Accept",
        )
