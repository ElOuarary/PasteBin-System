from typing import Annotated

from fastapi import Header, HTTPException, status


def content_type_validation(
    content_type: Annotated[str, Header()] = "application/json",
):
    if content_type.lower() != "application/json":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "application/json is the only supported value for the Content-Type"
            },
        )


def accept_validation(accept: Annotated[str | None, Header()] = None):
    if accept is not None and accept.lower() not in ("application/json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "application/json is only supported value for the Accept"},
        )
    if accept is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "application/json is needed in the request's header"},
        )
