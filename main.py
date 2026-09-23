from fastapi import FastAPI, status
from routers import auth, paste, pastes


app = FastAPI()
app.include_router(auth.router)
app.include_router(paste.router)
app.include_router(pastes.router)


@app.get("/health", status_code=status.HTTP_200_OK)
def root():
    return {"Status": "Healthy"}