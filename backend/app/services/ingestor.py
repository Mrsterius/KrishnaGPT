import os
from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from app.config import get_settings
from typing import Optional

settings = get_settings()

# In-memory cache — avoids reloading from disk on every request
# _vectorstore: FAISS | None = None
_vectorstore: Optional[FAISS] = None

def ingest_pdf(pdf_path: str) -> int:
    """Load a PDF, chunk it, embed with OpenAI, and persist to FAISS.

    Returns the number of chunks created.
    """
    global _vectorstore

    # 1. Load PDF pages directly with pypdf (faster than PyPDFLoader)
    reader = PdfReader(pdf_path)
    documents = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            documents.append(
                Document(page_content=text, metadata={"page": i, "source": pdf_path})
            )

    # 2. Split into overlapping chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ".", "!", "?", " ", ""],
    )
    chunks = splitter.split_documents(documents)

    # 3. Embed with OpenAI and build FAISS index
    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )
    os.makedirs(settings.faiss_index_path, exist_ok=True)
    _vectorstore = FAISS.from_documents(chunks, embeddings)
    _vectorstore.save_local(settings.faiss_index_path)

    return len(chunks)


def load_vectorstore() -> FAISS:
    """Return the in-memory vectorstore, loading from disk only once."""
    global _vectorstore
    if _vectorstore is None:
        embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )
        _vectorstore = FAISS.load_local(
            settings.faiss_index_path,
            embeddings,
            allow_dangerous_deserialization=True,
        )
    return _vectorstore
