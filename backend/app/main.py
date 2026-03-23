from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth
from app.routes import quiz
from app.routes import doubt
from app.routes import arena
from app.routes import mentor
from app.routes import vault
from app.routes import syllabus
from app.routes import mock_test
from app.routes import srs
from app.routes import planner
from app.routes import dashboard
from app.routes import adaptive
from app.core.database import connect_to_mongo, close_mongo_connection
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    await connect_to_mongo()
    yield
    # Shutdown logic
    await close_mongo_connection()

app = FastAPI(
    title="JEE/NEET/UPSC AI EdTech API",
    description="Competitive, AI-powered backend for aspirants (Refactored)",
    version="1.1.0",
    lifespan=lifespan
)

# CORS Middleware
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(quiz.router)
app.include_router(doubt.router)
app.include_router(arena.router)
app.include_router(mentor.router)
app.include_router(vault.router)
app.include_router(syllabus.router)
app.include_router(mock_test.router)
app.include_router(srs.router)
app.include_router(planner.router)
app.include_router(dashboard.router)
app.include_router(adaptive.router)

@app.get("/")
async def health_check():
    return {
        "status": "API is running", 
        "version": "1.1.0",
        "message": "Welcome to the refactored JEE/NEET/UPSC AI EdTech Platform"
    }
