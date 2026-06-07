import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, ingest
from app.config import get_settings

logger = logging.getLogger("uvicorn.info")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-ingest the Bhagavad Gita PDF on first startup if the FAISS index is missing."""
    index_file = os.path.join(settings.faiss_index_path, "index.faiss")
    default_pdf = os.path.join(settings.pdf_data_path, "bhagavad_gita.pdf")

    if not os.path.exists(index_file):
        if os.path.exists(default_pdf):
            logger.info(
                "🔍 No FAISS index found. Auto-ingesting '%s' on startup …", default_pdf
            )
            try:
                from app.services.ingestor import ingest_pdf
                chunks = ingest_pdf(default_pdf)
                logger.info("✅ Auto-ingestion complete — %d chunks indexed.", chunks)
            except Exception as exc:
                logger.error("❌ Auto-ingestion failed: %s", exc)
        else:
            logger.warning(
                "⚠️  No FAISS index and no PDF found at '%s'. "
                "Upload a PDF via POST /api/ingest/pdf or place 'bhagavad_gita.pdf' "
                "in the backend/data/ folder.",
                default_pdf,
            )
    else:
        logger.info("✅ FAISS index already exists — skipping auto-ingestion.")

    yield  # App runs here


app = FastAPI(
    title="Bhagavad Gita RAG API",
    description="A RAG-powered chatbot for the Bhagavad Gita using LangChain + OpenAI + FAISS",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(ingest.router)


@app.get("/")
async def root():
    return {
        "message": "Bhagavad Gita RAG API",
        "docs": "/api/docs",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
