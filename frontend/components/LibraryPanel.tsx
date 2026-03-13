'use client'
import { useState } from 'react'
import { apiFetch } from '@/lib/api'
import { LibraryResult } from '@/lib/types'

interface Props {
  showToast: (msg: string, type: 'success' | 'error') => void
}

const SUGGESTIONS = [
  'What is the role of place in marketing strategy?',
  'How do pricing models affect customer perception?',
  'Explain brand purpose and its business impact',
]

function formatText(text: string) {
  return text
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,'<em>$1</em>')
    .replace(/`(.+?)`/g,'<code>$1</code>')
    .replace(/\n/g,'<br/>')
}

export default function LibraryPanel({ showToast }: Props) {
  const [query, setQuery]   = useState('')
  const [result, setResult] = useState<LibraryResult | null>(null)
  const [loading, setLoading] = useState(false)

  const search = async (q?: string) => {
    const q_ = (q ?? query).trim()
    if (!q_ || loading) return
    if (q) setQuery(q)
    setLoading(true); setResult(null)
    try {
      const resp = await apiFetch<LibraryResult>('/library/search', 'POST', { query: q_ })
      setResult(resp)
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : 'Search failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-5 flex-shrink-0"
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="text-lg font-bold">📚 Digital Library</div>
        <span className="text-xs font-bold px-3 py-1 rounded-full"
          style={{ background: 'rgba(62,207,142,0.1)', color: '#3ecf8e', border: '1px solid rgba(62,207,142,0.22)' }}>
          Agentic RAG · 30 Chapters
        </span>
      </div>

      {/* Search bar */}
      <div className="px-8 py-5 flex-shrink-0" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex gap-3">
          <input type="text" value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && search()}
            placeholder="Search across all 30 chapters…"
            className="flex-1 px-4 py-3 rounded-xl text-sm text-btext outline-none transition-all"
            style={{ background: '#12122a', border: '1px solid rgba(255,255,255,0.09)' }}
            onFocus={e => (e.target.style.borderColor = '#3ecf8e')}
            onBlur={e  => (e.target.style.borderColor = 'rgba(255,255,255,0.09)')} />
          <button onClick={() => search()} disabled={loading || !query.trim()}
            className="px-6 py-3 rounded-xl font-bold text-sm transition-all disabled:opacity-40 flex-shrink-0"
            style={{ background: 'linear-gradient(135deg,#3ecf8e,#2eaf74)', color: '#0a1a14' }}
            onMouseEnter={e => !loading && (e.currentTarget.style.opacity='0.85')}
            onMouseLeave={e => (e.currentTarget.style.opacity='1')}>
            {loading ? <span className="spinner" style={{ borderTopColor: '#0a1a14' }} /> : 'Search'}
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {!result && !loading && (
          <div className="flex flex-col items-center justify-center text-center text-bmuted py-16 animate-fadeUp">
            <div className="text-5xl mb-4 opacity-40">📚</div>
            <div className="font-semibold text-btext mb-1">Search the knowledge base</div>
            <div className="text-sm mb-8">Agentic RAG searches across all 30 chapters with multi-round retrieval.</div>
            <div className="flex flex-col gap-2 w-full max-w-md">
              {SUGGESTIONS.map(s => (
                <button key={s} onClick={() => search(s)}
                  className="text-sm px-4 py-3 rounded-xl text-left transition-all"
                  style={{ background: 'rgba(62,207,142,0.06)', border: '1px solid rgba(62,207,142,0.15)', color: '#3ecf8e' }}
                  onMouseEnter={e => (e.currentTarget.style.background='rgba(62,207,142,0.12)')}
                  onMouseLeave={e => (e.currentTarget.style.background='rgba(62,207,142,0.06)')}>
                  🔍 {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center text-center py-20 animate-fadeUp">
            <div className="text-4xl mb-4 animate-bounce3">🔍</div>
            <div className="text-sm text-bmuted">Searching across 30 chapters…</div>
            <div className="flex gap-1 mt-4">
              <span className="dot" /><span className="dot" /><span className="dot" />
            </div>
          </div>
        )}

        {result && (
          <div className="animate-fadeUp">
            {/* Answer card */}
            <div className="rounded-2xl overflow-hidden mb-4"
              style={{ background: '#12122a', border: '1px solid rgba(255,255,255,0.07)' }}>
              {/* Card header */}
              <div className="px-5 py-3 flex items-center justify-between"
                style={{ background: 'rgba(62,207,142,0.06)', borderBottom: '1px solid rgba(62,207,142,0.12)' }}>
                <span className="text-xs font-bold uppercase tracking-wider" style={{ color: '#3ecf8e' }}>
                  📚 Library Answer
                </span>
                <div className="flex items-center gap-3 text-xs text-bmuted">
                  <span>RAG rounds: <strong className="text-btext">{result.rag_rounds || 1}</strong></span>
                  {result.latency_ms && <span>{result.latency_ms}ms</span>}
                </div>
              </div>
              {/* Answer body */}
              <div className="px-5 py-5 text-sm leading-7 text-btext bubble-content"
                dangerouslySetInnerHTML={{ __html: formatText(result.answer) }} />
              {/* Chapter chips */}
              {result.chapters_hit?.length > 0 && (
                <div className="px-5 pb-4 flex flex-wrap gap-2">
                  {result.chapters_hit.map(c => (
                    <span key={c} className="text-[0.68rem] font-semibold px-2.5 py-1 rounded-lg"
                      style={{ background: 'rgba(62,207,142,0.1)', border: '1px solid rgba(62,207,142,0.22)', color: '#3ecf8e' }}>
                      Ch. {c}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <button onClick={() => { setResult(null); setQuery('') }}
              className="text-xs text-bmuted hover:text-btext transition-colors">
              ← New search
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
