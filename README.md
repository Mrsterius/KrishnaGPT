# KrishnaGPT

A RAG-based chatbot application that provides intelligent responses based on the Bhagavad Gita.

## Features

- **FastAPI Backend**: Python-based API with FAISS vector search
- **React Frontend**: Modern UI built with Vite
- **RAG Pipeline**: Document ingestion, embedding, and retrieval
- **Guardrails**: Content moderation and evaluation system
- **Docker Support**: Containerized deployment with docker-compose

## Tech Stack

### Backend
- FastAPI
- OpenAI API (embeddings & LLM)
- FAISS vector database
- LangChain

### Frontend
- React
- Vite
- Modern CSS

## Setup

### Prerequisites
- Docker & Docker Compose
- OpenAI API key

### Environment Variables

Create a `.env` file in the `backend/` directory:
```bash
OPENAI_API_KEY=your-openai-api-key-here
```

See `backend/.env.example` for all available configuration options.

### Running with Docker

```bash
docker-compose up -d
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

### Running Locally

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
KrishnaGPT/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── routers/     # API endpoints
│   │   ├── services/    # Business logic
│   │   └── models.py    # Data models
│   ├── data/            # PDF source files
│   └── faiss_index/     # Vector database
├── frontend/            # React application
│   └── src/
│       └── components/  # UI components
└── docker-compose.yml   # Container orchestration
```

## API Endpoints

- `POST /api/ingest` - Upload and process PDF documents
- `POST /api/chat` - Send messages and receive responses
- `GET /health` - Health check endpoint

## License

MIT
