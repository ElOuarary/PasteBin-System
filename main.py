from fastapi import FastAPI, Body, Header, HTTPException, status

from typing import Annotated
import uuid

app = FastAPI()

memory = {}

@app.get("/health", status_code=status.HTTP_200_OK)
def root():
    return {"Status": "Healthy"}

@app.post("/pastebin", status_code=status.HTTP_201_CREATED)
def write_pin(
    text: str = Body(embed=True, max_length=10_000),
    content_type: Annotated[str | None, Header()] = None,
    accept: Annotated[str | None, Header()] = None
    ):
    if content_type is None or content_type.lower() != "application/json":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="application/json is only the supproted content_type")
    if accept is None or accept.lower() != "application/json":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="application/json is only the supproted accept")
    if text is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Please Provide the body parameter text")
    try:
        paste_id = str(uuid.uuid4())
        memory[paste_id] = text
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return {"paste_id": paste_id, "content": text}

@app.get("/pastebin/{paste_id}", status_code=status.HTTP_200_OK)
def read_pin(paste_id: str):
    if paste_id not in memory.keys():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paste ID not found")
    return memory[paste_id]

@app.put("/pastebin/{paste_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_bin(
    paste_id: str,
    text: str = Body(embed=True, max_length=10_000),
    content_type: Annotated[str | None, Header()] = None,
    accept: Annotated[str | None, Header()] = None
    ):
    if content_type is None or content_type.lower() != "application/json":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="application/json is only the supproted content_type")
    if accept is None or accept.lower() != "application/json":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="application/json is only the supproted accept")
    if paste_id not in memory.keys():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paste ID not found")
    memory[paste_id] = text
    return

@app.delete("/pastebin/{paste_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bin(paste_id: str):
    if paste_id not in memory.keys():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paste ID not found")
    memory.pop(paste_id)
    return