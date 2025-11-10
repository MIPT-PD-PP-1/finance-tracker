from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_db
from app.routes import users, groups, transactions

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="Finance Tracker API", lifespan=lifespan)

app.include_router(users.router)
app.include_router(groups.router)
app.include_router(transactions.router)

@app.get("/api")
async def read_root():
    return {"message": "This Finance Tracker API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

