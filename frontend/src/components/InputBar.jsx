import { useState, useRef, useEffect } from 'react'

export default function InputBar({ onSend, isLoading, isIndexed }) {
  const [input, setInput] = useState('')
  const textareaRef = useRef(null)

  const disabled = isLoading || !isIndexed

  const placeholder = !isIndexed
    ? 'First, ingest the Bhagavad Gita PDF using the left panel…'
    : isLoading
    ? 'Seeking wisdom from the Gita…'
    : 'Ask about dharma, karma, yoga, the soul, or any teaching…'

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setInput('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleChange = (e) => {
    setInput(e.target.value)
    // Auto-grow textarea
    e.target.style.height = 'auto'
    e.target.style.height = `${Math.min(e.target.scrollHeight, 150)}px`
  }

  return (
    <div className="input-bar">
      <div className="input-container">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="message-input"
        />
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="send-button"
        >
          ✦ Send
        </button>
      </div>
      <p className="input-hint">Enter to send · Shift+Enter for new line</p>
    </div>
  )
}
