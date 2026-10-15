from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from skills import router as skills_router
from learning import router as learning_router
from intelligence import router as intelligence_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="CapacityConnect API",
    description=(
        "Workforce skill intelligence, learning management, "
        "trainer matching and capacity simulation."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "CapacityConnect backend is running!",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/dashboard")
def dashboard():
    return {
        "employees": 248,
        "active_learners": 186,
        "active_courses": 32,
        "skill_gap_alerts": 12,
    }


app.include_router(skills_router)
app.include_router(learning_router)
app.include_router(intelligence_router)