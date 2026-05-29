import { useState, useEffect, useRef } from 'react'
import { newChatSession, sendChatMessage } from '../lib/api'
import type { ChatMessage } from '../types'

export function ChatPanel() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    newChatSession().then(setSessionId).catch(() => {})
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || !sessionId || sending) return
    const userMsg: ChatMessage = { role: 'user', content: input.trim() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setSending(true)
    try {
      const response = await sendChatMessage(sessionId, userMsg.content)
      setMessages(prev => [...prev, { role: 'assistant', content: response }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error al procesar el mensaje.' }])
    } finally {
      setSending(false)
    }
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="bg-card border border-border rounded-2xl flex flex-col h-80">
      <div className="px-6 py-4 border-b border-border">
        <h3 className="text-white font-bold text-lg">Consultas al sistema</h3>
        <p className="text-muted text-xs mt-0.5">Pregunta sobre el sistema o los análisis</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-muted text-sm text-center mt-8">
            Escribe una pregunta para comenzar
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] px-4 py-2 rounded-xl text-sm ${
                msg.role === 'user'
                  ? 'bg-[#4aa3ff] text-white'
                  : 'bg-[#2a2a2a] border border-border text-[#d0d0cc]'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex justify-start">
            <div className="bg-[#2a2a2a] border border-border px-4 py-2 rounded-xl text-muted text-sm animate-pulse">
              Escribiendo...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="px-6 py-4 border-t border-border flex gap-3">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Escribe tu consulta..."
          disabled={!sessionId || sending}
          className="flex-1 bg-[#1a1a1a] border border-border rounded-xl px-4 py-2 text-white text-sm placeholder-muted focus:outline-none focus:border-[#4aa3ff] disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || !sessionId || sending}
          className="px-5 py-2 rounded-xl bg-[#4aa3ff] text-white text-sm font-bold hover:bg-[#2d8ae8] disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          Enviar
        </button>
      </div>
    </div>
  )
}
