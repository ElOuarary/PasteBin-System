from fastapi import FastAPI, Body, Header, HTTPException, status

from typing import Annotated
import uuid

MAX_CHARACTER_ALLOWED = 10_000_000

app = FastAPI()

memory = {}

@app.get("/health", status_code=status.HTTP_200_OK)
def root():
    return {"Status": "Healthy"}

@app.post("/pastebin", status_code=status.HTTP_201_CREATED)
def write_pin(
    content: str = Body(embed=True, max_length=MAX_CHARACTER_ALLOWED),
    accept: Annotated[str | None, Header()] = None
    ):
    if accept is not None and accept.lower() != "application/json":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail={"error": "application/json is only the supproted Accept"})
    if content is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "Please Provide content in the request's body"})
    paste_id = str(uuid.uuid4())
    memory[paste_id] = content
    return {"paste_id": paste_id}

@app.get("/pastebin/{paste_id}", status_code=status.HTTP_200_OK)
def read_pin(
    paste_id: str,
    accept: Annotated[str | None, Header()] = None
    ):
    if accept is not None and accept.lower() != "application/json":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error" : "application/json is only the supproted Accept"})
    if paste_id not in memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"})
    return {"content": memory[paste_id]}

@app.put("/pastebin/{paste_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_bin(
    paste_id: str,
    content: str = Body(embed=True, max_length=MAX_CHARACTER_ALLOWED),
    accept: Annotated[str | None, Header()] = None
    ):
    if accept is not None and accept.lower() != "application/json":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail={"error": "application/json is only the supproted accept"})
    if paste_id not in memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"})
    memory[paste_id] = content
    return

@app.delete("/pastebin/{paste_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bin(paste_id: str):
    if paste_id not in memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "not found"})
    memory.pop(paste_id)
    return