import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import EvalBadge from './EvalBadge'

export default function MessageBubble({ message }) {
  const [showSources, setShowSources] = useState(false)
  const isUser = message.role === 'user'

  return (
    <div className={`message-wrapper ${isUser ? 'user' : 'assistant'}`}>
      {/* Avatar */}
      <div className={`avatar ${isUser ? 'user-avatar' : ''}`}>
        {isUser ? '🙏' : 'ॐ'}
      </div>

      {/* Bubble */}
      <div className={`message-bubble ${isUser ? 'bubble-user' : 'bubble-assistant'}`}>
        {/* Guardrail warning banner */}
        {message.guardrailTriggered && message.guardrailMessage && (
          <div className="guardrail-banner">⚠️ {message.guardrailMessage}</div>
        )}

        {/* Content */}
        {isUser ? (
          <p style={{ margin: 0 }}>{message.content}</p>
        ) : (
          <div className="markdown-content">
            {/* Show pulsing dots when streaming hasn't produced text yet */}
            {message.isStreaming && message.content === '' ? (
              <div className="thinking-dots">
                <div className="dot" />
                <div className="dot" />
                <div className="dot" />
              </div>
            ) : (
              <>
                <ReactMarkdown>{message.content}</ReactMarkdown>
                {/* Blinking cursor while tokens are still arriving */}
                {message.isStreaming && (
                  <span className="cursor-blink">▊</span>
                )}
              </>
            )}
          </div>
        )}

        {/* Sources — shown after streaming completes */}
        {!isUser && !message.isStreaming && message.sources && message.sources.length > 0 && (
          <div className="sources-section">
            <button
              className="sources-toggle"
              onClick={() => setShowSources((v) => !v)}
            >
              📜 {message.sources.length} Source{message.sources.length > 1 ? 's' : ''}{' '}
              {showSources ? '▲' : '▼'}
            </button>
            {showSources && (
              <div className="sources-list">
                {message.sources.map((src, i) => (
                  <div key={i} className="source-item">
                    <span className="source-page">Page {src.page}</span>
                    <p className="source-content">{src.content}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Evaluation badges — shown after streaming completes */}
        {!isUser && !message.isStreaming && message.evaluation && (
          <div className="eval-section">
            <EvalBadge
              label="Faithful"
              score={message.evaluation.faithfulness}
              color="#7c6fcf"
            />
            <EvalBadge
              label="Relevant"
              score={message.evaluation.answer_relevance}
              color="#5ba358"
            />
            <EvalBadge
              label="Context"
              score={message.evaluation.context_relevance}
              color="#c9a227"
            />
          </div>
        )}
      </div>
    </div>
  )
}
