from typing import AsyncIterator, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from app.config import get_settings

settings = get_settings()

RAG_SYSTEM_PROMPT = """\
You are a profound spiritual guide and scholar of the Bhagavad Gita — the eternal \
dialogue between Lord Krishna and Arjuna on the battlefield of Kurukshetra.

Your purpose is to illuminate the Gita's timeless wisdom for modern seekers. \
Speak with warmth, depth, and reverence.

GUIDELINES:
1. Answer ONLY based on the provided context from the Bhagavad Gita.
2. If the context lacks sufficient information, acknowledge it gracefully and guide \
   the seeker to reflect further.
3. Quote relevant shlokas (verses) if they appear in the context.
4. Connect teachings to practical life where appropriate.
5. Use uplifting, spiritual language.

Context from the Bhagavad Gita:
{context}

Previous Conversation:
{chat_history}"""

RAG_PROMPT = ChatPromptTemplate.from_messages(
    [("system", RAG_SYSTEM_PROMPT), ("human", "{question}")]
)


def format_docs(docs) -> str:
    return "\n\n---\n\n".join(
        f"[Page {doc.metadata.get('page', '?')}]\n{doc.page_content}" for doc in docs
    )


def format_chat_history(history: List[dict]) -> str:
    if not history:
        return "This is the start of our conversation."
    lines = []
    for turn in history[-5:]:  # Keep last 5 exchanges to stay within context limits
        lines.append(f"Human: {turn.get('human', '')}")
        lines.append(f"Assistant: {turn.get('assistant', '')}")
    return "\n".join(lines)


def retrieve_docs(vectorstore: FAISS, question: str):
    """Retrieve top-k relevant chunks using MMR for diversity."""
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": settings.retriever_k, "fetch_k": 3},
    )
    return retriever.invoke(question)


def generate_answer(docs, question: str, chat_history: List[dict] = []) -> str:
    """Synchronous answer generation (used by non-streaming endpoint)."""
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        openai_api_key=settings.openai_api_key,
    )
    chain = RAG_PROMPT | llm | StrOutputParser()
    return chain.invoke(
        {
            "context": format_docs(docs),
            "question": question,
            "chat_history": format_chat_history(chat_history),
        }
    )


async def stream_answer(
    docs, question: str, chat_history: List[dict] = []
) -> AsyncIterator[str]:
    """Async generator that yields answer tokens for SSE streaming."""
    llm = ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        openai_api_key=settings.openai_api_key,
        streaming=True,
    )
    chain = RAG_PROMPT | llm | StrOutputParser()
    async for chunk in chain.astream(
        {
            "context": format_docs(docs),
            "question": question,
            "chat_history": format_chat_history(chat_history),
        }
    ):
        yield chunk
