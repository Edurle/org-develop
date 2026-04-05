from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, init_mongo, close_mongo
from app.routers import auth as auth_router
from app.routers import teams as teams_router
from app.routers import projects as projects_router
from app.routers import iterations as iterations_router
from app.routers import requirements as requirements_router
from app.routers import specifications as specifications_router
from app.routers import tasks as tasks_router
from app.routers import testcases as testcases_router
from app.routers import coverage as coverage_router
from app.routers import audit as audit_router
from app.routers import users as users_router
from app.routers import webhooks as webhooks_router
import app.models  # noqa: F401 — register all models


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables (dev mode), init MongoDB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_mongo()
    yield
    # Shutdown: clean up
    await close_mongo()


app = FastAPI(
    title="Spec-Driven Dev Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


app.include_router(auth_router.router)
app.include_router(teams_router.router)
app.include_router(projects_router.router)
app.include_router(iterations_router.router)
app.include_router(requirements_router.router)
app.include_router(specifications_router.router)
app.include_router(tasks_router.router)
app.include_router(testcases_router.router)
app.include_router(coverage_router.router)
app.include_router(webhooks_router.router)
app.include_router(audit_router.router)
app.include_router(users_router.router)
