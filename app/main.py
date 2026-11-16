import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models import Receipt
from app.routers import receipts
from app.services.samples import seed_samples

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

FRONTEND_BUILD = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Samples are added only when the database is first created, so they
    # stay deleted once the user removes them.
    is_new_database = not inspect(engine).has_table(Receipt.__tablename__)
    Base.metadata.create_all(engine)

    if is_new_database and get_settings().seed_sample_data:
        with SessionLocal() as db:
            count = seed_samples(db)
        logger.info("New database: added %s sample receipts", count)

    yield


app = FastAPI(
    title="Receipt Scanner API",
    description="Upload a receipt photo and get clean, validated, structured data.",
    version="1.0.0",
    lifespan=lifespan,
)

# The Vite dev server runs on a different port, so it needs CORS during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(receipts.router)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "extractor": get_settings().extractor}


# In production (and Docker) the built React app is served by FastAPI itself.
# Mounted last so it never shadows the API routes.
if FRONTEND_BUILD.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD, html=True), name="frontend")
