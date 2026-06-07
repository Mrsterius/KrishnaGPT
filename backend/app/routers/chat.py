import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models import ChatRequest, ChatResponse, Source
from app.services.ingestor import load_vectorstore
from app.services.rag_chain import retrieve_docs, generate_answer, stream_answer, format_docs
from app.services.guardrails import check_input_guardrail, check_output_guardrail
from app.services.evaluator import evaluate_response
from app.config import get_settings

router = APIRouter(prefix="/api/chat", tags=["Chat"])
settings = get_settings()


def _assert_index_exists():
    if not os.path.exists(os.path.join(settings.faiss_index_path, "index.faiss")):
        raise HTTPException(
            status_code=503,
            detail=(
                "Knowledge base not indexed yet. "
                "Please upload and ingest the Bhagavad Gita PDF via POST /api/ingest/pdf"
            ),
        )


# ---------------------------------------------------------------------------
# POST /api/chat/stream  — Server-Sent Events (SSE) streaming endpoint
# ---------------------------------------------------------------------------
@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """
    SSE streaming chat with guardrails and post-generation evaluation.

    Event types sent to the client:
      {"type": "token",    "content": "..."}       – partial answer chunk
      {"type": "metadata", "sources": [...], "evaluation": {...}, ...}
      {"type": "guardrail","content": "..."}        – input blocked
      {"type": "error",    "content": "..."}        – server error
      data: [DONE]                                  – stream complete
    """
    _assert_index_exists()

    async def event_generator():
        # 1. Input guardrail
        is_allowed, guard_msg = check_input_guardrail(request.message)
        if not is_allowed:
            yield f"data: {json.dumps({'type': 'guardrail', 'content': guard_msg})}\n\n"
            yield "data: [DONE]\n\n"
            return

        # 2. Retrieve relevant chunks
        vectorstore = load_vectorstore()
        docs = retrieve_docs(vectorstore, request.message)
        context = format_docs(docs)

        # 3. Stream answer tokens
        full_answer = ""
        try:
            async for chunk in stream_answer(docs, request.message, request.chat_history or []):
                full_answer += chunk
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"
            yield "data: [DONE]\n\n"
            return

        # 4. Output guardrail + evaluation
        is_safe, out_guard_msg = check_output_guardrail(full_answer, context)
        eval_scores = evaluate_response(request.message, full_answer, context)

        # 5. Build sources list and send metadata
        sources = [
            {"page": doc.metadata.get("page", 0) + 1, "content": doc.page_content[:350]}
            for doc in docs
        ]
        metadata_payload = {
            "type": "metadata",
            "sources": sources,
            "evaluation": eval_scores,
            "guardrail_triggered": not is_safe,
            "guardrail_message": out_guard_msg if not is_safe else None,
        }
        yield f"data: {json.dumps(metadata_payload)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# POST /api/chat/  — Standard (non-streaming) endpoint
# ---------------------------------------------------------------------------
@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Full response with sources, evaluation scores, and guardrails."""
    _assert_index_exists()

    is_allowed, guard_msg = check_input_guardrail(request.message)
    if not is_allowed:
        return ChatResponse(
            answer=guard_msg,
            sources=[],
            guardrail_triggered=True,
            guardrail_message=guard_msg,
        )

    vectorstore = load_vectorstore()
    docs = retrieve_docs(vectorstore, request.message)
    context = format_docs(docs)
    answer = generate_answer(docs, request.message, request.chat_history or [])

    is_safe, out_guard_msg = check_output_guardrail(answer, context)
    eval_scores = evaluate_response(request.message, answer, context)

    sources = [
        Source(page=doc.metadata.get("page", 0) + 1, content=doc.page_content[:350])
        for doc in docs
    ]

    return ChatResponse(
        answer=answer,
        sources=sources,
        evaluation=eval_scores,
        guardrail_triggered=not is_safe,
        guardrail_message=out_guard_msg if not is_safe else None,
    )
