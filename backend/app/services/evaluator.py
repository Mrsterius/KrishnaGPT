import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from app.config import get_settings

settings = get_settings()

_EVAL_PROMPT = PromptTemplate(
    input_variables=["question", "answer", "context"],
    template="""You are an strict expert evaluator for RAG (Retrieval-Augmented Generation) systems.

Evaluate the following on a scale of 0.0 to 1.0:

Question: {question}

Context (retrieved from Bhagavad Gita):
{context}

Generated Answer:
{answer}

Scoring criteria:
1. faithfulness       – How factually consistent is the answer with the context?
                        (A score between 0.0 and 1.0, where 1.0 means the answer is fully supported by the context, and 0.0 means it is completely contradicted or fabricated.)
2. answer_relevance   – How well does the answer address the question?
                        (A score between 0.0 and 1.0, where 1.0 means the answer is perfectly on-topic, and 0.0 means it is completely off-topic.)
3. context_relevance  – How relevant is the retrieved context to the question?
                        (A score between 0.0 and 1.0, where 1.0 means the context is highest relevant, and 0.0 means it is completely irrelevant.)

Respond ONLY with a JSON object — no markdown, no explanation:
{{"faithfulness": 0.xx, "answer_relevance": 0.xx, "context_relevance": 0.xx}}""",
)


def evaluate_response(question: str, answer: str, context: str) -> dict:
    """LLM-based RAG evaluation. Returns dict with three float scores."""
    try:
        llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=0,
            openai_api_key=settings.openai_api_key,
        )
        chain = _EVAL_PROMPT | llm
        result = chain.invoke(
            {"question": question, "answer": answer, "context": context}
        )
        raw = result.content.strip()
        # Strip any accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        scores = json.loads(raw)
        return {
            "faithfulness": float(max(0.0, min(1.0, scores.get("faithfulness", 0.5)))),
            "answer_relevance": float(
                max(0.0, min(1.0, scores.get("answer_relevance", 0.5)))
            ),
            "context_relevance": float(
                max(0.0, min(1.0, scores.get("context_relevance", 0.5)))
            ),
        }
    except Exception:
        return {"faithfulness": 0.5, "answer_relevance": 0.5, "context_relevance": 0.5}
