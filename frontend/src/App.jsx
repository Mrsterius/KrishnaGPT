import { useState, useEffect, useCallback } from 'react'
import ChatWindow from './components/ChatWindow'
import InputBar from './components/InputBar'
import Sidebar from './components/Sidebar'

// In development, Vite proxies /api/* → localhost:8000 (see vite.config.js)
// In production, nginx proxies it. Leave VITE_API_URL empty for relative paths.
const API_URL = import.meta.env.VITE_API_URL || ''

const WELCOME_MESSAGE_READY = {
  id: 'welcome',
  role: 'assistant',
  content: `**Namaste** 🙏\n\nI am your guide to the timeless wisdom of the **Bhagavad Gita** — the divine dialogue between Lord Krishna and Arjuna on the battlefield of Kurukshetra.\n\nThe knowledge base is **ready**. Ask me anything about *dharma*, *karma*, *yoga*, the nature of the soul, or any of Krishna's teachings.`,
  sources: [],
  evaluation: null,
  guardrailTriggered: false,
  isStreaming: false,
}

const WELCOME_MESSAGE_NOT_READY = {
  ...WELCOME_MESSAGE_READY,
  content: `**Namaste** 🙏\n\nI am your guide to the timeless wisdom of the **Bhagavad Gita**.\n\n⏳ The backend is **indexing the PDF** on startup — this takes about a minute. The sidebar will turn green once it's ready. You can also upload your own PDF using the left panel.`,
}

export default function App() {
  const [messages, setMessages] = useState([WELCOME_MESSAGE_NOT_READY])
  const [isLoading, setIsLoading] = useState(false)
  const [isIndexed, setIsIndexed] = useState(false)
  const [isAutoIngesting, setIsAutoIngesting] = useState(false)
  const [chatHistory, setChatHistory] = useState([])

  // Poll until the FAISS index is ready (handles auto-ingestion on startup)
  useEffect(() => {
    let attempts = 0
    const maxAttempts = 40 // poll for up to ~2 minutes

    const poll = async () => {
      try {
        const res = await fetch(`${API_URL}/api/ingest/status`)
        if (res.ok) {
          const data = await res.json()
          if (data.indexed) {
            setIsIndexed(true)
            setIsAutoIngesting(false)
            setMessages([WELCOME_MESSAGE_READY])
            return // stop polling
          } else {
            setIsAutoIngesting(true)
          }
        }
      } catch {
        // backend starting up — keep polling
      }
      attempts++
      if (attempts < maxAttempts) {
        setTimeout(poll, 3000)
      }
    }

    poll()
  }, [])

  const sendMessage = useCallback(
    async (userMessage) => {
      if (!userMessage.trim() || isLoading) return

      const userMsg = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: userMessage,
      }

      const assistantId = `assistant-${Date.now()}`
      const assistantPlaceholder = {
        id: assistantId,
        role: 'assistant',
        content: '',
        sources: [],
        evaluation: null,
        guardrailTriggered: false,
        isStreaming: true,
      }

      setMessages((prev) => [...prev, userMsg, assistantPlaceholder])
      setIsLoading(true)

      try {
        const response = await fetch(`${API_URL}/api/chat/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: userMessage,
            chat_history: chatHistory,
          }),
        })

        if (!response.ok) {
          throw new Error(`Server responded with ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let fullAnswer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() ?? '' // Keep the incomplete trailing line

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const data = line.slice(6).trim()
            if (data === '[DONE]') break

            let parsed
            try {
              parsed = JSON.parse(data)
            } catch {
              continue
            }

            if (parsed.type === 'token') {
              fullAnswer += parsed.content
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: fullAnswer } : m
                )
              )
            } else if (parsed.type === 'metadata') {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? {
                        ...m,
                        sources: parsed.sources ?? [],
                        evaluation: parsed.evaluation,
                        guardrailTriggered: parsed.guardrail_triggered,
                        guardrailMessage: parsed.guardrail_message,
                        isStreaming: false,
                      }
                    : m
                )
              )
              setChatHistory((prev) => [
                ...prev,
                { human: userMessage, assistant: fullAnswer },
              ])
            } else if (parsed.type === 'guardrail') {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? {
                        ...m,
                        content: parsed.content,
                        guardrailTriggered: true,
                        isStreaming: false,
                      }
                    : m
                )
              )
            } else if (parsed.type === 'error') {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, content: `⚠️ ${parsed.content}`, isStreaming: false }
                    : m
                )
              )
            }
          }
        }
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content:
                    '⚠️ Could not reach the server. Please ensure the backend is running.',
                  isStreaming: false,
                }
              : m
          )
        )
      } finally {
        setIsLoading(false)
      }
    },
    [isLoading, chatHistory]
  )

  const clearChat = () => {
    setMessages([WELCOME_MESSAGE])
    setChatHistory([])
  }

  return (
    <div className="app">
      <Sidebar
        isIndexed={isIndexed}
        isAutoIngesting={isAutoIngesting}
        onIndexed={setIsIndexed}
        apiUrl={API_URL}
        onSuggest={sendMessage}
      />
      <main className="main-content">
        <div className="chat-header">
          <span className="chat-header-title">⚔ Wisdom of Kurukshetra</span>
          <button className="btn-clear" onClick={clearChat}>
            Clear Chat
          </button>
        </div>
        <ChatWindow messages={messages} />
        <InputBar
          onSend={sendMessage}
          isLoading={isLoading}
          isIndexed={isIndexed}
        />
      </main>
    </div>
  )
}
