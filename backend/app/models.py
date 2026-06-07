from pydantic import BaseModel
from typing import Optional, List


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    chat_history: Optional[List[dict]] = []


class Source(BaseModel):
    page: int
    content: str


class EvaluationScores(BaseModel):
    faithfulness: float
    answer_relevance: float
    context_relevance: float


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    evaluation: Optional[EvaluationScores] = None
    guardrail_triggered: bool = False
    guardrail_message: Optional[str] = None


class IngestResponse(BaseModel):
    status: str
    chunks_created: int
    message: str
