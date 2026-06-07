import { useState, useRef } from 'react'

const SUGGESTED_QUESTIONS = [
  'What is the essence of dharma?',
  'Explain karma yoga in simple terms',
  'How does Krishna describe the eternal soul?',
  'What does the Gita say about detachment?',
  'How can one overcome fear and grief?',
  'What is the path to moksha (liberation)?',
  'What are the three types of yoga?',
]

export default function Sidebar({ isIndexed, isAutoIngesting, onIndexed, apiUrl, onSuggest }) {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState('')
  const fileInputRef = useRef(null)

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    e.target.value = '' // Reset so the same file can be re-selected if needed

    setIsUploading(true)
    setUploadMsg('⏳ Processing PDF…')

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${apiUrl}/api/ingest/pdf`, {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      if (res.ok) {
        setUploadMsg(`✓ ${data.chunks_created} chunks indexed!`)
        onIndexed(true)
      } else {
        setUploadMsg(`✗ ${data.detail ?? 'Upload failed'}`)
      }
    } catch {
      setUploadMsg('✗ Could not reach the backend')
    } finally {
      setIsUploading(false)
    }
  }

  const handleIngestDefault = async () => {
    setIsUploading(true)
    setUploadMsg('⏳ Ingesting default PDF…')
    try {
      const res = await fetch(`${apiUrl}/api/ingest/default`, { method: 'POST' })
      const data = await res.json()
      if (res.ok) {
        setUploadMsg(`✓ ${data.chunks_created} chunks indexed!`)
        onIndexed(true)
      } else {
        setUploadMsg(`✗ ${data.detail ?? 'Failed'}`)
      }
    } catch {
      setUploadMsg('✗ Could not reach the backend')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <aside className="sidebar">
      {/* ── Header ── */}
      <div className="sidebar-header">
        <span className="om-symbol">ॐ</span>
        <h1 className="sidebar-title">Bhagavad Gita</h1>
        <p className="sidebar-subtitle">Divine Wisdom Guide</p>
      </div>

      {/* ── Index Status ── */}
      <div
        className={`status-indicator ${
          isIndexed ? 'indexed' : isAutoIngesting ? 'ingesting' : 'not-indexed'
        }`}
      >
        <span className="status-dot" />
        <span>
          {isIndexed
            ? 'Knowledge Base Ready'
            : isAutoIngesting
            ? 'Indexing PDF on startup…'
            : 'Not Indexed — Upload PDF'}
        </span>
      </div>

      {/* ── PDF Ingestion ── */}
      <div className="ingest-section">
        <p className="section-label">PDF Ingestion</p>

        <button
          className="btn-primary"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
        >
          📄 Upload Bhagavad Gita PDF
        </button>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileUpload}
          style={{ display: 'none' }}
          aria-label="Upload PDF"
        />

        <button
          className="btn-secondary"
          onClick={handleIngestDefault}
          disabled={isUploading}
          title="Uses backend/data/bhagavad_gita.pdf"
        >
          🗄️ Use Default PDF (backend/data/)
        </button>

        {uploadMsg && (
          <p
            className={`upload-message ${
              uploadMsg.startsWith('✓') ? 'success' : 'error'
            }`}
          >
            {uploadMsg}
          </p>
        )}
      </div>

      {/* ── Suggested Questions ── */}
      <div className="suggestions-section">
        <p className="section-label">Suggested Questions</p>
        <div className="suggestions-list">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              className="suggestion-btn"
              onClick={() => onSuggest(q)}
              disabled={!isIndexed}
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* ── Footer ── */}
      <div className="sidebar-footer">
        <p className="footer-text">
          OpenAI GPT-4o-mini · LangChain · FAISS
          <br />
          Guardrails · RAG Evaluation
        </p>
      </div>
    </aside>
  )
}
