import { useState, useRef, useEffect } from 'react'
import ChatHeader from './components/ChatHeader'
import MessageList from './components/MessageList'
import ChatInput from './components/ChatInput'
import './App.css'

const API_BASE = 'http://localhost:8000'
const DEMO_MESSAGE = `**Backend unreachable**

Ensure the API server is running:
- \`cd backend && uvicorn main:app --port 8000\`
- Set GROQ_API_KEY in backend/.env for live AI

See RUN-UI.md for full steps.`

function App() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: `**Welcome to SOP Copilot**

I'm your administrative AI SOP assistant.

Quick actions: Ask "What is SOP?" or about compliance, DPI incident response, or dashboard review.`,
      timestamp: new Date().toISOString(),
    },
  ])
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async (text, imageFile = null) => {
    if (!text.trim() && !imageFile) return

    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      image: imageFile ? URL.createObjectURL(imageFile) : null,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text.trim() }),
      })

      const data = await res.json()

      if (!res.ok) {
        console.error('Backend error:', res.status, data)
        setMessages((prev) => [
          ...prev,
          {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: data?.reply && typeof data.reply === 'string' ? data.reply : DEMO_MESSAGE,
            timestamp: new Date().toISOString(),
          },
        ])
        return
      }

      const reply = data?.reply != null ? String(data.reply).trim() : ''
      const assistantMsg = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: reply || DEMO_MESSAGE,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      console.error('Backend unreachable:', err)
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: DEMO_MESSAGE,
          timestamp: new Date().toISOString(),
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app">
      <ChatHeader />
      <MessageList messages={messages} isLoading={isLoading} />
      <div ref={messagesEndRef} />
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  )
}

export default App
