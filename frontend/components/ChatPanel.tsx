'use client'
import { useState, useRef, useEffect } from 'react'
import { apiFetch } from '@/lib/api'
import { ChatMsg } from '@/lib/types'

interface Props {
  showToast: (msg: string, type: 'success' | 'error') => void
}

function agentBadge(agent?: string) {
  if (!agent) return null
  const isProf = agent.startsWith('professor') || agent.startsWith('prof') || agent.startsWith('place')
  const isCoach = agent === 'coach'
  const isDean  = agent === 'dean'
  const label   = agent.replace(/_/g, ' ').replace('professor ', 'Prof. ')
  const style = isProf  ? { bg: 'rgba(124,92,191,0.15)', color: '#9b7de0', border: 'rgba(124,92,191,0.3)' }
              : isCoach ? { bg: 'rgba(62,207,142,0.15)',  color: '#3ecf8e', border: 'rgba(62,207,142,0.3)' }
              : isDean  ? { bg: 'rgba(79,172,254,0.15)',  color: '#4facfe', border: 'rgba(79,172,254,0.3)' }
              :           { bg: 'rgba(155,125,224,0.15)', color: '#9b7de0', border: 'rgba(155,125,224,0.3)' }
  return (
    <span className="text-[0.62rem] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border"
      style={{ background: style.bg, color: style.color, borderColor: style.border }}>
      {label}
    </span>
  )
}

function formatText(text: string) {
  return text
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/`(.+?)`/g,'<code>$1</code>')
    .replace(/\n/g,'<br/>')
}

export default function ChatPanel({ showToast }: Props) {
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [openThinking, setOpenThinking] = useState<Set<string>>(new Set())
  const bottomRef = useRef<HTMLDivElement>(null)
  const taRef     = useRef<HTMLTextAreaElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages, loading])

  const send = async () => {
    const msg = input.trim()
    if (!msg || loading) return
    setInput('')
    if (taRef.current) { taRef.current.style.height = 'auto' }

    const userMsg: ChatMsg = { id: Date.now().toString(), role: 'user', text: msg }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const resp = await apiFetch<{ text: string; source_agent?: string; thinking?: string; latency_ms?: number; rag_chunks?: number }>('/chat', 'POST', { message: msg })
      const aiMsg: ChatMsg = {
        id: Date.now().toString() + '_ai',
        role: 'assistant',
        text: resp.text,
        source_agent: resp.source_agent,
        thinking: resp.thinking,
        latency_ms: resp.latency_ms,
        rag_chunks: resp.rag_chunks,
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (e: unknown) {
      const err = e instanceof Error ? e.message : 'Request failed'
      setMessages(prev => [...prev, { id: Date.now().toString()+'_err', role: 'assistant', text: `⚠️ ${err}`, source_agent: 'error' }])
      showToast(err, 'error')
    } finally {
      setLoading(false)
      taRef.current?.focus()
    }
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  const toggleThinking = (id: string) => {
    setOpenThinking(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-5 flex-shrink-0"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="text-lg font-bold">💬 Chat with Dean Morgan</div>
        <span className="text-xs font-bold px-3 py-1 rounded-full"
          style={{ background: 'rgba(124,92,191,0.1)', color: '#9b7de0', border: '1px solid rgba(124,92,191,0.22)' }}>
          3-Tier Pipeline
        </span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-8 py-6 flex flex-col gap-5">
        {messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-bmuted py-20 animate-fadeUp">
            <div className="text-5xl mb-4 opacity-40">💬</div>
            <div className="font-semibold text-btext mb-1">Start a conversation</div>
            <div className="text-sm">Ask anything about business, marketing, or strategy.<br />Dean Morgan routes your question to the right professor.</div>
            <div className="flex gap-3 mt-6 flex-wrap justify-center">
              {['What is footfall analysis?','Explain the 10 P\'s of business','How does pricing strategy work?'].map(q => (
                <button key={q} onClick={() => { setInput(q); taRef.current?.focus() }}
                  className="text-xs px-4 py-2 rounded-xl transition-all"
                  style={{ background: 'rgba(124,92,191,0.1)', border: '1px solid rgba(124,92,191,0.22)', color: '#9b7de0' }}
                  onMouseEnter={e=>(e.currentTarget.style.background='rgba(124,92,191,0.18)')}
                  onMouseLeave={e=>(e.currentTarget.style.background='rgba(124,92,191,0.1)')}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(m => (
          <div key={m.id} className={`flex gap-3 max-w-3xl animate-fadeUp ${m.role === 'user' ? 'self-end flex-row-reverse' : 'self-start'}`}>
            {/* Avatar */}
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5"
              style={m.role === 'user'
                ? { background: 'linear-gradient(135deg,#7c5cbf,#9b7de0)' }
                : { background: '#1a1a3a', border: '1px solid rgba(255,255,255,0.1)' }}>
              {m.role === 'user' ? '👤' : '🎓'}
            </div>

            <div className="flex flex-col gap-1.5">
              {/* Meta */}
              <div className={`flex items-center gap-2 text-[0.68rem] ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                {m.role === 'user'
                  ? <span className="font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border text-[0.62rem]"
                      style={{ background: 'rgba(255,217,61,0.1)', color: '#ffd93d', borderColor: 'rgba(255,217,61,0.25)' }}>You</span>
                  : agentBadge(m.source_agent)
                }
                {m.latency_ms && <span className="text-bmuted">{m.latency_ms}ms</span>}
              </div>

              {/* Bubble */}
              <div className="px-4 py-3 rounded-2xl text-sm leading-relaxed bubble-content"
                style={m.role === 'user'
                  ? { background: 'rgba(124,92,191,0.2)', border: '1px solid rgba(124,92,191,0.3)' }
                  : { background: '#12122a', border: '1px solid rgba(255,255,255,0.07)' }}
                dangerouslySetInnerHTML={{ __html: formatText(m.text) }} />

              {/* Thinking */}
              {m.thinking && (
                <>
                  <button onClick={() => toggleThinking(m.id)}
                    className="flex items-center gap-1.5 text-xs text-bmuted hover:text-btext transition-colors">
                    <span>🧠</span>
                    <span>Extended Thinking</span>
                    <span>{openThinking.has(m.id) ? '▼' : '▶'}</span>
                  </button>
                  {openThinking.has(m.id) && (
                    <div className="px-4 py-3 rounded-xl text-xs text-bmuted leading-relaxed max-w-xl animate-fadeUp"
                      style={{ background: 'rgba(255,217,61,0.04)', border: '1px solid rgba(255,217,61,0.14)' }}>
                      {m.thinking}
                    </div>
                  )}
                </>
              )}

              {/* RAG chips */}
              {m.rag_chunks && m.rag_chunks > 0 && (
                <div className="flex gap-2">
                  <span className="text-[0.62rem] px-2 py-0.5 rounded-md"
                    style={{ background: 'rgba(62,207,142,0.08)', border: '1px solid rgba(62,207,142,0.2)', color: '#3ecf8e' }}>
                    📄 {m.rag_chunks} chunks
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div className="flex gap-3 self-start animate-fadeUp">
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs"
              style={{ background: '#1a1a3a', border: '1px solid rgba(255,255,255,0.1)' }}>🎓</div>
            <div className="flex items-center gap-1.5 px-4 py-3 rounded-2xl"
              style={{ background: '#12122a', border: '1px solid rgba(255,255,255,0.07)' }}>
              <span className="dot" /><span className="dot" /><span className="dot" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-8 py-4 flex gap-3 items-end flex-shrink-0"
        style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <textarea ref={taRef} rows={1} value={input}
          onChange={e => {
            setInput(e.target.value)
            e.target.style.height = 'auto'
            e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
          }}
          onKeyDown={onKeyDown}
          placeholder="Ask Dean Morgan anything…"
          className="flex-1 px-4 py-3 rounded-xl text-sm text-btext resize-none outline-none transition-all"
          style={{ background: '#12122a', border: '1px solid rgba(255,255,255,0.09)', maxHeight: '120px', fontFamily: 'inherit', lineHeight: '1.5' }}
          onFocus={e => (e.target.style.borderColor = '#7c5cbf')}
          onBlur={e  => (e.target.style.borderColor = 'rgba(255,255,255,0.09)')} />
        <button onClick={send} disabled={loading || !input.trim()}
          className="px-5 py-3 rounded-xl font-semibold text-white text-sm transition-all flex-shrink-0 disabled:opacity-40"
          style={{ background: 'linear-gradient(135deg,#7c5cbf,#5a3f9e)' }}
          onMouseEnter={e=>!loading && (e.currentTarget.style.opacity='0.85')}
          onMouseLeave={e=>(e.currentTarget.style.opacity='1')}>
          {loading ? <span className="spinner" /> : 'Send ↑'}
        </button>
      </div>
    </div>
  )
}
