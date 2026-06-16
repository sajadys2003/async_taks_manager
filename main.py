from fastapi import FastAPI
from app.api.v1 import auth, jobs

app = FastAPI(title="Cloud Resource Management API")

app.include_router(auth.router)
app.include_router(jobs.router)

@app.get("/")
def root():
    return {"message": "API is running"}
