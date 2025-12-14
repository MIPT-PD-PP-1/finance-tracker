from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes import users, groups, transactions
from app.scheduler import start_scheduler, shutdown_scheduler, check_reminders

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    shutdown_scheduler()

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

@app.get("/reminders")
async def call_reminders():
    await check_reminders()
    return

