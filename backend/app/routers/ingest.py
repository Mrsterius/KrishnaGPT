import os
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.models import IngestResponse
from app.services.ingestor import ingest_pdf
from app.config import get_settings

router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])
settings = get_settings()

_ALLOWED_MIME = {"application/pdf"}


@router.post("/pdf", response_model=IngestResponse)
def ingest_pdf_upload(file: UploadFile = File(...)):
    """Upload a PDF and ingest it into the FAISS vector store."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    os.makedirs(settings.pdf_data_path, exist_ok=True)
    # Sanitise filename — avoid path traversal
    safe_name = os.path.basename(file.filename)
    pdf_path = os.path.join(settings.pdf_data_path, safe_name)

    content = file.file.read()
    with open(pdf_path, "wb") as f:
        f.write(content)

    try:
        chunks = ingest_pdf(pdf_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return IngestResponse(
        status="success",
        chunks_created=chunks,
        message=f"'{safe_name}' ingested successfully into {chunks} chunks.",
    )


@router.post("/default", response_model=IngestResponse)
def ingest_default():
    """Ingest the pre-placed bhagavad_gita.pdf from the backend/data/ folder."""
    pdf_path = os.path.join(settings.pdf_data_path, "bhagavad_gita.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=404,
            detail=(
                "Default PDF not found. "
                "Place 'bhagavad_gita.pdf' inside the backend/data/ folder."
            ),
        )
    try:
        chunks = ingest_pdf(pdf_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return IngestResponse(
        status="success",
        chunks_created=chunks,
        message=f"Bhagavad Gita ingested into {chunks} chunks.",
    )


@router.get("/status")
def ingest_status():
    """Check whether the FAISS index has been built."""
    indexed = os.path.exists(
        os.path.join(settings.faiss_index_path, "index.faiss")
    )
    return {"indexed": indexed, "index_path": settings.faiss_index_path}
