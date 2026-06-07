from typing import Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from app.config import get_settings

settings = get_settings()

_GITA_TOPICS = (
    "Bhagavad Gita, Krishna, Arjuna, dharma, karma, yoga, spirituality, philosophy, "
    "Hindu scripture, moksha, Vedanta, meditation, soul, atman, Brahman, devotion, "
    "detachment, duty, righteousness, reincarnation, liberation, Kurukshetra, shloka, "
    "bhakti, jnana, raja yoga, Mahabharata, Upanishads, self-realization"
)

_INPUT_GUARD_PROMPT = PromptTemplate(
    input_variables=["question", "topics"],
    template="""You are a content filter for a Bhagavad Gita chatbot.

Decide if the question is relevant to the Bhagavad Gita, its teachings, or related \
spiritual / philosophical topics.

Allowed topics: {topics}

Question: {question}

Rules:
- If the question is about the Bhagavad Gita, Hindu philosophy, spirituality, dharma, \
  karma, yoga, life purpose, ethics, meditation, or any related topic → respond "ALLOWED"
- If the question is completely unrelated (coding help, weather, sports scores, political \
  opinions) → respond "BLOCKED"
- When in doubt, lean toward "ALLOWED"

Respond with ONLY the word ALLOWED or BLOCKED.
Response:""",
)

_OUTPUT_GUARD_PROMPT = PromptTemplate(
    input_variables=["answer", "context"],
    template="""You are a factual accuracy checker for a Bhagavad Gita RAG system.

Context retrieved from the Bhagavad Gita:
{context}

Generated answer:
{answer}

Does the answer make claims clearly NOT supported by or directly contradicted by the context?
Respond with ONLY "SAFE" or "UNSAFE".
Response:""",
)


def check_input_guardrail(question: str) -> Tuple[bool, str]:
    """Returns (is_allowed, user_facing_message)."""
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0,
        openai_api_key=settings.openai_api_key,
    )
    chain = _INPUT_GUARD_PROMPT | llm
    result = chain.invoke({"question": question, "topics": _GITA_TOPICS})
    is_allowed = "ALLOWED" in result.content.upper()
    message = (
        ""
        if is_allowed
        else (
            "This question falls outside the scope of the Bhagavad Gita chatbot. "
            "Please ask about the Gita's teachings, dharma, karma, yoga, or related "
            "spiritual topics. \U0001f64f"
        )
    )
    return is_allowed, message


def check_output_guardrail(answer: str, context: str) -> Tuple[bool, str]:
    """Returns (is_safe, user_facing_warning)."""
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=0,
        openai_api_key=settings.openai_api_key,
    )
    chain = _OUTPUT_GUARD_PROMPT | llm
    result = chain.invoke({"answer": answer, "context": context})
    is_safe = "SAFE" in result.content.upper()
    warning = (
        ""
        if is_safe
        else "Note: parts of this answer may not be fully grounded in the source text."
    )
    return is_safe, warning
